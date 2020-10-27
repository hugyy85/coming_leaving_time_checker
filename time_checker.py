from xml.etree.ElementTree import iterparse
import time

# get an iterable
context = iterparse('new.xml', events=("start", "end"))


for event, elem in context:
    elem.clear()
    # while elem.getprevious() is not None:
    #     del elem.getparent()[0]
del context
# for event, elem in context:
#     if event == "end" and elem.tag == "person":
#         context.root.clear()

# for event, elem in iterparse('new.xml', events=("start", "end")):
#     elem.clear()