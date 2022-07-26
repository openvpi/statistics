import datetime
import json

import pytz

import analysis
import download


def update():
    # Get yesterday
    tz = pytz.timezone('Asia/Shanghai')
    today = datetime.datetime.now(tz=tz)
    today_fmt = today.strftime('%Y-%m-%d')
    print('Today is:', today_fmt)
    yesterday = (today - datetime.timedelta(days=1))
    yesterday_fmt = yesterday.strftime('%Y-%m-%d')

    # Read data from file
    with open('data.json', 'r', encoding='utf-8') as f:
        history_data = json.load(f)
    if today.strftime('%Y-%m-%d') == history_data['date']:
        print('Everything is up to date!')
        return

    # Download and analysis log
    download.downloadDirFromCos(yesterday_fmt.replace('-', '/'))
    yesterday_data = analysis.analysisDate(yesterday_fmt)
    for item in yesterday_data:
        print(item)

    # Initialize numbers
    converter = history_data['converter']
    if len(converter['downloads']['recent']) >= 10:
        converter['downloads']['recent'] = converter['downloads']['recent'][1:]
    converter['downloads']['recent'].append(0)

    plugin_nums = {}
    for plugin in history_data['plugins']:
        plugin_nums[plugin['filename']] = 0
        if yesterday.weekday() == 0:
            plugin['downloads']['weekly'] = 0
        else:
            plugin['downloads']['weekly'] += plugin['downloads']['yesterday']

    # Update numbers
    for item in yesterday_data:
        number = item['downloads']
        if item['product'] == converter['filename']:
            converter['downloads']['recent'][-1] = number
            converter['downloads']['total'] += number
        else:
            plugin_nums[item['product']] = number
    for plugin in history_data['plugins']:
        plugin['downloads']['yesterday'] = plugin_nums[plugin['filename']]
        plugin['downloads']['total'] += plugin['downloads']['yesterday']

    # Write back new data
    history_data['date'] = today_fmt
    with open('data.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(history_data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    update()
