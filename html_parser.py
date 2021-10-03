from html.parser import HTMLParser

data_handler = None
mnemonic = None

instructions = []

def handle_mode(name):
    global data_handler
    instructions.append((mnemonic, name))
    data_handler = None

def handle_mnemonic(name):
    global data_handler, mnemonic
    mnemonic = name
    data_handler = handle_mode

class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global data_handler
        if tag == 'font':
            data_handler = handle_mnemonic

    def handle_data(self, data):
        global data_handler
        if data_handler:
            data_handler(data.strip())

with open('65CE02.html', 'rb') as f:
    data = f.read().decode('cp1252')

parser = MyHTMLParser()
parser.feed(data)

accum_str = ''
count = 0
for inst in instructions:
    count += 1
    name, mode = inst
    split_mode = mode.split()
    if len(split_mode):
        mode = split_mode[0]
    if mode.isdigit():
        mode = ''
    accum_str += f'{name}{mode}'
    if (count % 16) == 0:
        print(accum_str)
        accum_str = ''
    else:
        accum_str += ','

