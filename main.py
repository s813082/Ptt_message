import requests,json
import datetime
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import date

def clould_text(message_fileurl,cloud_fileurl):
    with open(message_fileurl, encoding="utf-8", errors='ignore') as f:
        text = f.read()

    text = replace_useless_text(text)
    # 設定使用 big5 斷詞
    jieba.set_dictionary('dict.txt.big')
    wordlist = jieba.cut(text)
    words = " ".join(wordlist)
    # print(words)

    #背景顏色預設黑色，改為白色、使用指定字體
    myWordClode = WordCloud(background_color='white',font_path='SourceHanSansTW-Regular.otf',width=1920,height=1080,min_font_size=10).generate(words)

    # 用PIL顯示文字雲
    plt.imshow(myWordClode)
    plt.axis("off")
    plt.show()

    # 儲存結果圖
    myWordClode.to_file(cloud_fileurl)

def write_message_text(fileurl,message_list):
    f = open(fileurl, 'w', encoding='UTF-8')
    for i in range(len(message_list)):
        # print(stock.messageList[i])
        f.write(message_list[i] + '\n')
    f.close()

def replace_useless_text(text):
    useless_list = ["的","喔","啊","嗎","了","就","要","哦","我","都","被"]

    for useless in useless_list:
        text = text.replace(useless,"")
    return text

# 分析文章中所有的留言訊息
def analysis_data(entries_list):
    message_list = []
    title_list = []
    for post in entries_list:
        title = post.get("title")
        if title not in title_list:
            message_content = ''
            message_dict = post.get("pushes")
            if message_dict != None:
                for message in message_dict:
                    raw_message = message.get("content").replace(": ","")
                    message_content = message_content + raw_message
                message_list.append(message_content)
                title_list.append(title)
            else:
                # 如果發文就不列入追蹤
                continue
    return message_list

# 遞迴取得所有文章
def loop_get_message_list(year_firstday,year_lastday,search_account,page,per_page,entries_list):
    page = page + 1
    url = 'https://www.plytic.com/api/v1/authors/'+search_account+'?page='+str(page)+'&per_page='+per_page
    ptt_data = requests.get(url)
    if ptt_data.status_code == 200:
        print(f"{page}. 成功取得{per_page}筆資料")
        data_dict = json.loads(ptt_data.text)
        # 拿到資料最後一筆的留言日期
        activities_dict = data_dict.get("activities")
        entries = activities_dict.get("entries")
        last_message_dict = entries[-1].get("pushes")
        last_message_time_string = last_message_dict[0].get("pushed_at")
        last_message_time_split = last_message_time_string.split("T")
        last_message_time = datetime.datetime.strptime(last_message_time_split[0], "%Y-%m-%d")
        if last_message_time > year_firstday and last_message_time < year_lastday:
            entries_list = entries_list + entries
            entries_list = loop_get_message_list(year_firstday,year_lastday,search_account,page,per_page,entries_list)
            return entries_list
        else:
            temp_entries_list = []
            for post in entries:
                pushes = post.get("pushes")
                if pushes != None:
                    push_time_string = pushes[0].get("pushed_at")
                    push_time_string_split = push_time_string.split("T")
                    push_time = datetime.datetime.strptime(push_time_string_split[0], "%Y-%m-%d")
                    if push_time >= year_firstday and push_time < year_lastday:
                        temp_entries_list.append(post)
                    else:
                        break
                else:
                    continue
            entries_list = entries_list + temp_entries_list
            return entries_list
    else:
        raise Exception(f"Get Url : {url} failed status code: {ptt_data.status_code}")


# 輸入要查詢帳號
search_account = input("請輸入要搜尋的帳號 : ")
today = date.today()
message_filename = str(today)+"_message.txt"
clould_filename = str(today)+"_clould.png"
message_fileurl = f'./{message_filename}'
cloud_fileurl = f'./{clould_filename}'
page = 0
per_page = "20"
entries_list = []
year_firstday = datetime.datetime(2021,1,1)
year_lastday = datetime.datetime(2021,12,31)
try:
    print(f"開始取得自 {year_firstday.date()} ~ {year_lastday.date()} {search_account}的所有文章")
    entries_list = loop_get_message_list(year_firstday,year_lastday,search_account,page,per_page,entries_list)
    print(f"總共取得 {len(entries_list)}筆資料")
    message_list = analysis_data(entries_list)
    print(f"將留言資料寫入紀錄檔")
    write_message_text(message_fileurl,message_list)
    print(f"開始製作文字雲")
    clould_text(message_fileurl,cloud_fileurl)
except Exception as e:
    print(f"錯誤訊息 : {e}")