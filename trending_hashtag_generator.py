# -*- coding: utf-8 -*-

import wx
import wx.lib.scrolledpanel as scrolled
from pytrends.request import TrendReq
import pandas as pd
import jieba
import jieba.analyse
import jieba.posseg as pseg
from opencc import OpenCC
from concurrent.futures import ThreadPoolExecutor
import time

# ----------------------
# 參數設定
# ----------------------
if_popular = 0.1
how_fast = 1
howlong_sleep = 3

sym_words = []
sym_class_words = []

# ----------------------
# 同義詞讀取
# ----------------------
with open('raw_txt.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    line = line.strip()
    items = line.split(' ')
    index = items[0]
    if index.endswith('='):
        sym_words.append(items[1:])
    if index.endswith('#'):
        sym_class_words.append(items[1:])

# ----------------------
# 功能定義
# ----------------------
def get_sym(w, word_set):
    results = []
    if len(w) == 1:
        for each in word_set:
            if w in each:
                results.append(each)
    else:
        for each in word_set:
            if any(w in word for word in each):
                results.append(each)
    return results

def get_good_friends(friend):
    pytrend = TrendReq(hl='en-US', tz=360, timeout=(10,25))
    global tag_pocket

    cc = OpenCC('s2twp')
    friend = cc.convert(friend)
    if tag_master == friend:
        return

    keywords = [tag_master, friend]
    pytrend.build_payload(kw_list=keywords, cat=0, timeframe='today 1-m', geo='TW', gprop='')

    df = pd.DataFrame(pytrend.interest_over_time())
    print(tag_master, friend)
    if not df.empty and tag_master in df.columns and friend in df.columns:
        print(df[tag_master].mean(), df[friend].mean())
        if if_popular * df[tag_master].mean() < df[friend].mean():
            tag_pocket.append(friend)

    time.sleep(howlong_sleep)
    print()

# ----------------------
# GUI
# ----------------------
class HashtagGeneratorFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='熱門標籤生成器 v0.1', size=(600, 700))

        panel = scrolled.ScrolledPanel(self)
        panel.SetupScrolling()
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 輸入區域
        input_box = wx.StaticBox(panel, label="輸入設定")
        input_sizer = wx.StaticBoxSizer(input_box, wx.VERTICAL)
        self.text_input = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(550, 100))
        input_sizer.Add(self.text_input, 0, wx.EXPAND | wx.ALL, 5)

        # 參數區域
        param_box = wx.StaticBox(panel, label="參數設定")
        param_sizer = wx.StaticBoxSizer(param_box, wx.VERTICAL)
        param_grid = wx.FlexGridSizer(cols=2, vgap=5, hgap=5)

        param_grid.Add(wx.StaticText(panel, label="人氣門檻:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.popularity_ctrl = wx.TextCtrl(panel, value=str(if_popular))
        param_grid.Add(self.popularity_ctrl, 0, wx.EXPAND)

        param_grid.Add(wx.StaticText(panel, label="執行緒數量:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.thread_ctrl = wx.TextCtrl(panel, value=str(how_fast))
        param_grid.Add(self.thread_ctrl, 0, wx.EXPAND)

        param_grid.Add(wx.StaticText(panel, label="延遲(秒):"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.delay_ctrl = wx.TextCtrl(panel, value=str(howlong_sleep))
        param_grid.Add(self.delay_ctrl, 0, wx.EXPAND)

        param_sizer.Add(param_grid, 0, wx.EXPAND | wx.ALL, 5)

        # 輸出區域
        output_box = wx.StaticBox(panel, label="輸出結果")
        output_sizer = wx.StaticBoxSizer(output_box, wx.VERTICAL)

        self.output_ig = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(550, 100))
        output_sizer.Add(wx.StaticText(panel, label="Instagram 標籤:"), 0, wx.ALL, 5)
        output_sizer.Add(self.output_ig, 0, wx.EXPAND | wx.ALL, 5)

        self.output_yt = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(550, 100))
        output_sizer.Add(wx.StaticText(panel, label="YouTube 標籤:"), 0, wx.ALL, 5)
        output_sizer.Add(self.output_yt, 0, wx.EXPAND | wx.ALL, 5)

        # 生成按鈕
        generate_btn = wx.Button(panel, label="生成標籤")
        generate_btn.Bind(wx.EVT_BUTTON, self.on_generate)

        vbox.Add(input_sizer, 0, wx.EXPAND | wx.ALL, 10)
        vbox.Add(param_sizer, 0, wx.EXPAND | wx.ALL, 10)
        vbox.Add(generate_btn, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        vbox.Add(output_sizer, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(vbox)
        self.Centre()

    def on_generate(self, event):
        global if_popular, how_fast, howlong_sleep

        try:
            if_popular = float(self.popularity_ctrl.GetValue())
            how_fast = int(self.thread_ctrl.GetValue())
            howlong_sleep = int(self.delay_ctrl.GetValue())
        except ValueError:
            wx.MessageBox("請輸入有效的數字！", "錯誤", wx.OK | wx.ICON_ERROR)
            return

        input_text = self.text_input.GetValue()
        if not input_text:
            wx.MessageBox("請輸入要分析的文字！", "錯誤", wx.OK | wx.ICON_ERROR)
            return

        self.process_text(input_text)

    def process_text(self, text):
        global tag_master, tag_pocket

        cc = OpenCC('tw2sp')
        text = cc.convert(text)
        tag_pocket = []

        keywords = jieba.analyse.extract_tags(text, topK=10, withWeight=True, allowPOS=('n','nr','ns','nrt','nrf','nrj'))

        for item, v in keywords:
            test_list = []
            precache = get_sym(item, sym_words)

            cc2 = OpenCC('s2twp')
            tag_master = cc2.convert(item)
            tag_pocket.append(tag_master)

            print(f"主關鍵字: {tag_master}")

            if precache:
                print(f"同義詞：{precache}")
                for j in precache:
                    for i in j:
                        test_list.append(i)

            if item in test_list:
                test_list.remove(item)

            print(f"相關詞列表：{test_list}")

            with ThreadPoolExecutor(max_workers=how_fast) as executor:
                executor.map(get_good_friends, test_list)

        meow = list(set(tag_pocket))
        meow2 = []

        cc = OpenCC('tw2sp')
        for i in meow:
            for w, tag in jieba.posseg.cut(cc.convert(i)):
                if len(w) == 1:
                    if not 'n' in tag:
                        continue
                meow2.append(OpenCC('s2twp').convert(w))

        ig_tags = ' '.join([f'#{i}' for i in meow2])
        yt_tags = ', '.join(meow2)

        self.output_ig.SetValue(ig_tags)
        self.output_yt.SetValue(yt_tags)

# ----------------------
# 啟動
# ----------------------
if __name__ == '__main__':
    app = wx.App(False)
    frame = HashtagGeneratorFrame()
    frame.Show()
    app.MainLoop()
