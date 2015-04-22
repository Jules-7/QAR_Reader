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
             383:  ["an74",  "bur3_analog",  384,    0.12],
             391:  ["s340",  "qar_sound",    384,    0.03],
             3911: ["s340",  "qar_no_sound", 384,    1],
             401:  ["b737",  "qar",          None,   None],
             402:  ["b737",  "dfdr_980",     384,    5],
             4022: ["b737",  "dfdr_980_I",   384,    4],
             403:  ["b737",  "4700",         768,    4],
             411:  ["an12",  "msrp12",       512,    0.5],
             421:  ["an140", "bur92",        512,    1]}


# ------|User id|-|username through code|-|name of prog window|-|program window size|
ACCESS = {1:       ["admin",          "admin",                  (900, 500), ['b747.bmp',
                                                                            'a320.bmp',
                                                                            'an148.bmp',
                                                                            'an32.bmp',
                                                                            'an26.bmp',
                                                                            'an72.bmp',
                                                                            'an74.bmp',
                                                                            's340.bmp',
                                                                            'b737.bmp',
                                                                            'open_CF.png',
                                                                            'save_raw.png',
                                                                            '12_16.png',
                                                                            'an12.png',
                                                                            'test.png',
                                                                            'an140.bmp']],

          10:      ["yanair",           "YanAir",               (600, 500), ['a320.bmp',
                                                                             's340.bmp',
                                                                             'open_CF.png',
                                                                             'b737.bmp']],

          11:      ["gap_ukraine", u'ГАП "Украина" Ан148 БУР-92 А-05', (600, 500), []],

          12:      ["VCH",                 u'В/Ч №2269',        (600, 500), ['an26.bmp',
                                                                             'an72.bmp',
                                                                             'an74.bmp']],

          13:      ["bukovina",           u"Буковина",           (600, 500), []],

          14:      ["mak",                   u"МАК",             (600, 500), ['bur92.bmp']]}

ARINC_DIRECT = {1: "001001000111",  # 247
                2: "010110111000",  # 5b8
                3: "101001000111",  # a47
                4: "110110111000"}  # db8

ARINC_REVERSE = {1: "111000100100",  # e24
                 2: "000111011010",  # 1da
                 3: "111000100101",  # e25
                 4: "000111011011"}  # 1db

HEADER_SIZE = 128  # Monstr

# all qar_types id must be registered here
MONSTR_HEADER_TYPES = [321, 351, 361, 371, 381, 382, 383, 391, 3911, 403, 411]
OWN_HEADER_TYPES = [322]
NO_HEADER_TYPES = [331, 341, 401, 402, 4022, 421]