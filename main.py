
head = '''<?xml version="1.0" encoding="UTF-8"?>
    <people>'''
end = '''</people>'''
a = '''
    <person full_name="i.ivanov">
    <start>21-12-2011 10:54:47</start>
    <end>21-12-2011 19:43:02</end>
    </person>
    <person full_name="a.stepanova">
    <start>21-12-2011 09:40:10</start>
    <end>21-12-2011 17:59:15</end>
    </person>
'''
with open('new.xml', 'w') as f:
    f.write(head)
    for i in range(10000000):
        f.write(a)

    f.write(end)