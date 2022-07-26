import datetime
import json
import os
import re
import shlex


def group(ls, key):
    d = {}
    for e in ls:
        k = str(key(e))
        if k in d:
            d[k].append(e)
        else:
            d[k] = [e]
    res = [(k, d[k]) for k in d]
    res.sort(key=lambda x: x[0])
    return res


def parse(line):
    item = shlex.split(line)
    if item[5] == 'GETObject' and not item[11].startswith('/log') and item[14].startswith('2'):
        product_full_name = re.search(r'opensvip_((converter)|(plugin_[\da-z]*))_\d+\.\d+\.\d+', item[11]).group()
        return True, {
            'time': item[3],
            'ip': item[6],
            'product': product_full_name[9:],
            'agent': item[13]
        }
    else:
        return False, None


def read(path):
    arr = []
    with open(path, 'r') as file:
        line = file.readline()
        while line:
            match, item = parse(line)
            if match:
                arr.append(item)
            line = file.readline()
    return arr


def raw(date=None):
    items = []
    if date is not None:
        path = os.path.join('logs', date)
        for log in os.listdir(path):
            items += read(os.path.join(path, log))
    else:
        for year in os.listdir('logs'):
            year_dir = os.path.join('logs', year)
            for month in os.listdir(year_dir):
                month_dir = os.path.join(year_dir, month)
                for day in os.listdir(month_dir):
                    day_dir = os.path.join(month_dir, day)
                    for log in os.listdir(day_dir):
                        items += read(os.path.join(day_dir, log))
    return items


def file_rank(items):
    rank = []
    file_groups = group(items, key=lambda x: x['product'])
    for file_gp in file_groups:
        rank.append({
            'product': file_gp[0][:file_gp[0].rindex('_')],
            'downloads': len(group(file_gp[1], key=lambda x: x['ip']))
        })
    version_groups = group(rank, key=lambda x: x['product'])
    res = []
    for version_gp in version_groups:
        total = 0
        for item in version_gp[1]:
            total += item['downloads']
        res.append({
            'product': version_gp[0],
            'downloads': total
        })

    res.sort(key=lambda x: x['downloads'], reverse=True)
    return res


def analysisDate(date_str):
    date_data = raw(date_str.replace('-', '/'))
    return file_rank(date_data)


if __name__ == '__main__':
    arr = []
    date = datetime.date.today()
    for _ in range(10):
        date = (date - datetime.timedelta(days=1))
        data = file_rank(raw(date.strftime('%Y-%m-%d').replace('-', '/')))
        for obj in data:
            if obj['product'] == 'converter':
                arr.append(obj['downloads'])
                break
    arr = arr[::-1]
    print('recent:', arr[-10:])
    print('total:', sum(arr))
    print()
    with open('data.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    for plugin in config['plugins']:
        arr = []
        date = datetime.date.today()
        for _ in range(10):
            date = (date - datetime.timedelta(days=1))
            data = file_rank(raw(date.strftime('%Y-%m-%d').replace('-', '/')))
            for obj in data:
                if obj['product'] == plugin['filename']:
                    arr.append(obj['downloads'])
                    break
        arr = arr[::-1]
        plugin['downloads']['yesterday'] = arr[-1]
        plugin['downloads']['weekly'] = 0
        plugin['downloads']['total'] = sum(arr)
    with open('data.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(config, ensure_ascii=False, indent=2))

    # print(f'========== Yesterday ({date}) ==========')
    # for r in file_rank(data):
    #     print(r)
    # print()
    # data = raw(None)
    # print('============= Total statistics =============')
    # for r in file_rank(data):
    #     print(r)
