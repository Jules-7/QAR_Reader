#-*-coding: utf-8-*-

# admin
USER = 1
#-----------|id|---|acft|----|qar|-----|frame, B|--|duration, sec|
QAR_TYPES = {321:  ["a320",  "qar",          768,    4],
             322:  ["a320",  "cf",           768,    2],
             331:  ["b747",  "qar",          512,    4],
             341:  ["an148", "bur92",        512,    1],
             351:  ["an32",  "testerU32",    512,    1],
             361:  ["an26",  "msrp12",       512,    0.5],
             371:  ["an72",  "testerU32",    512,    1],
             381:  ["an74",  "bur3",         384,    0.12],
             382:  ["an74",  "bur3_code",    384,    0.12],
             391:  ["s340",  "qar_sound",    384,    0.03],
             3911: ["s340",  "qar_no_sound", 384,    1],
             401:  ["b737",  "qar",          None,   None],
             402:  ["b737",  "dfdr_980",     None,   None],
             403:  ["b737",  "4700",         768,    4],
             411:  ["an12",  "msrp12",       512,    0.5]}

# ------|User id|-|username through code|-|name of prog window|-|program window size|
ACCESS = {1:       ["admin",               "admin",                       (900, 500)],
          10:      ["yanair",              "YanAir",                      (600, 500)],
          11:      ["gap_ukraine",    u'ГАП "Украина" Ан148 БУР-92 А-05', (600, 500)],
          12:      ["VCH",                 u'В/Ч №2269',                  (600, 500)]}
