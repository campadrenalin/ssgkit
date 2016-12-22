#!/usr/bin/env python3

import ssgkit as kit
ssg = kit.SSG()
for p in ssg.pages:
    print(p.get_html())
print(ssg.layouts)

if __name__ == '__main__':
    ssg.build()
