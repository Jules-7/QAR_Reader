#-*-coding: utf-8-*-

# admin
USER = 1
# -----------|id|---|acft|----|qar|-----|frame, B for   |--|duration, sec|--|frame, B for  |
# -----------|  |---|    |----|   |-----|data processing|--|             |--|flights search|
QAR_TYPES = {321:  ["a320",  "qar",             768,        4],
             322:  ["a320",  "cf",              768,        2],
             331:  ["b747",  "qar",             512,        4],  # 200
             3312: ["b747",  "4700",            384,        5,                 512],  # 300
             341:  ["an148", "bur92",           512,        1],
             351:  ["an32",  "testerU32",       512,        1],
             361:  ["an26",  "msrp12",          512,        0.5],
             371:  ["an72",  "testerU32",       512,        1],
             381:  ["an74",  "bur3",            384,        0.12],
             382:  ["an74",  "bur3_code",       384,        0.12],
             383:  ["an74",  "bur3_analog",     384,        0.0467],
             391:  ["s340",  "qar_sound",       384,        0.03],
             3911: ["s340",  "qar_no_sound",    384,        1],
             401:  ["b737",  "qar_arinc",      None,       None],
             402:  ["b737",  "dfdr_980",        384,        5],
             4022: ["b737",  "dfdr_980_I",      384,        4],
             4031: ["b737",  "dfdr_980_BDB",    384,        5],
             4032: ["b737",  "dfdr_980_BDO",    384,        5],
             4033: ["b737",  "dfdr_980_BDV",    384,        5],
             403:  ["b737",  "qar_4700_analog", 768,        4],
             4034: ["b737",  "qar_4700",        384,        4],
             404:  ["b737",  "qar_ng",          1536,       4],
             411:  ["an12",  "msrp12",          512,        0.5],
             421:  ["an140", "bur92",           512,        1],
             501:  ["il76",  "msrp64",          512,        2],
             5011: ["il76",  "msrp64_viewer",   512,        2],
             601:  ["mi24",  "bur4T",           160,        4],
             701:  ["b767",  "qar",             1536,       4]}


# ------|User id|-|username through code|-|Program window|-|program window|-|list of bitmaps to be included|
# ------|       |-|                     |-|title         |-|size          |-|at executable build           |
ACCESS = {1:       ["admin",          "admin",                (950, 800), ['b747.png',
                                                                            'a320.png',
                                                                            'an148.png',
                                                                            'an32.png',
                                                                            'an26.png',
                                                                            'an72.png',
                                                                            'an74.png',
                                                                            's340.png',
                                                                            'b737.png',
                                                                            'open_CF.png',
                                                                            'save_raw.png',
                                                                            '12_16.png',
                                                                            'an12.png',
                                                                            'test.png',
                                                                            'an140.png',
                                                                            'har_dig.png',
                                                                            'il76.png',
                                                                            '10_16.png',
                                                                            'mi24.png',
                                                                            'b767.png']],

          10:      ["yanair",           "YanAir",               (600, 500), ['a320.png',
                                                                             's340.png',
                                                                             'open_CF.png',
                                                                             'b737.png']],

          11:      ["gap_ukraine", u'ГАП "Украина" Ан148 БУР-92 А-05', (600, 500), []],

          12:      ["VCH2269",             u'В/Ч №2269',        (600, 500), ['an26.png',
                                                                             'an72.png',
                                                                             'an74.png']],

          13:      ["bukovina",           u"Буковина",           (600, 500), []],

          14:      ["mak",                   u"МАК",             (600, 500), ['bur92.png']],

          15:      ["badr_airlines",      "Badr Airlines",       (600, 500), ['b737.png']],

          16:      ["il76",                   u"Ил76",           (600, 500), ['il76.png']],

          17:      ["VCH1604",            u'В/Ч A1604',          (600, 500), ['mi24.png']]}

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
# it is used for determining how to process data further for flights search
MONSTR_HEADER_TYPES = [321, 351, 361, 371, 381, 382, 383, 391, 3911, 403, 411, 501, 4034]
OWN_HEADER_TYPES = [322, 5011, 701, 404]
NO_HEADER_TYPES = [331, 3312, 341, 401, 402, 4022, 4031, 4032, 4033, 421, 601]


# each button holds information for corresponding bitmap button display onclick
A320_BUTTON = {'name': 'A320',
               'choices': {'QAR': 321, 'Compact Flash': 322},
               'default_choice': 321}

B747_BUTTON = {'name': 'B747',
               'choices': {'B747-200': 331, 'B747-300': 3312},
               'default_choice': 331}

AN148_BUTTON = {'name': u"Aн148",
                'choices': {u"БУР-92 А-05": 341},
                'default_choice': 341}

AN32_BUTTON = {'name': u"Aн32",
               'choices': {u"Тестер У3-2": 351},
               'default_choice': 351}

AN26_BUTTON = {'name': u"Aн26",
               'choices': {u"МСРП-12": 361},
               'default_choice': 361}

AN72_BUTTON = {'name': u"Aн72",
               'choices': {u"Тестер У3-2": 371},
               'default_choice': 371}

AN74_BUTTON = {'name': u"Aн74",
               'choices': {u"БУР-3": 381, u"БУР-3 код": 382, u"БУР-3 аналог": 383},
               'default_choice': 381}

S340_BUTTON = {'name': "S340",
               'choices': {u"QAR(with sound)": 391, u"QAR(no sound)": 3911},
               'default_choice': 391}

AN12_BUTTON = {'name': u"Aн12",
               'choices': {u"МСРП-12": 411},
               'default_choice': 411}

# il 76 choices
il76_choices = {u"МСРП-64": 501, u"МСРП-64-viewer": 5011}
if ACCESS[USER][0] == "admin":
    il76_choices = {u"МСРП-64": 501, u"МСРП-64-viewer": 5011}
elif ACCESS[USER][0] == "il76":
    il76_choices = {u"МСРП-64": 5011}

IL76_BUTTON = {'name': u"Ил76",
               'choices': il76_choices,
               'default_choice': 501}

MI24_BUTTON = {'name': u"Ми-24",
               'choices': {u"Бур-4Т": 601},
               'default_choice': 601}

B767_BUTTON = {'name': 'B767',
               'choices': {'QAR': 701},
               'default_choice': 701}

BUTTONS = {"a320": A320_BUTTON,
           "b747": B747_BUTTON,
           "an148": AN148_BUTTON,
           "an32": AN32_BUTTON,
           "an26": AN26_BUTTON,
           "an72": AN72_BUTTON,
           "an74": AN74_BUTTON,
           "s340": S340_BUTTON,
           "an12": AN12_BUTTON,
           "il76": IL76_BUTTON,
           "mi24": MI24_BUTTON,
           "b767": B767_BUTTON}


# def b737_button(self, event):
#         self.chosen_acft_type = 401
#         name = "B737"
#         choices = []
#         if ACCESS[USER][0] == "admin":
#             choices = ["QAR", "DFDR 980", "DFDR 980 I", "4700"]
#         elif ACCESS[USER][0] == "yanair":
#             choices = ["DFDR 980"]
#         elif ACCESS[USER][0] == "bukovina":
#             choices = ["DFDR 980 I"]
#         elif ACCESS[USER][0] == "badr_airlines":
#             choices = ["DFDR 980"]
#         option = self.make_choice_window(name, choices)
#         if option == "QAR":  # save this file with extension .inf to target place
#             self.chosen_acft_type = 401
#             self.get_path_to_file()
#             if self.path:
#                 self.get_path_to_save()
#                 flight = Flight(self.progress_bar, start=None, end=None, path=self.path,
#                                 name=None, chosen_acft_type=self.chosen_acft_type,
#                                 path_to_save=self.path_to_save)
#         elif option == "DFDR 980":  # different fdr types
#             dfdr_choices = ["default", "BDB", "BDO", "BDV"]
#             dfdr_type = self.make_choice_window(name, dfdr_choices)
#             if dfdr_type == "default":
#                 self.chosen_acft_type = 402
#             elif dfdr_type == "BDB":
#                 self.chosen_acft_type = 4031
#             elif dfdr_type == "BDO":
#                 self.chosen_acft_type = 4032
#             elif dfdr_type == "BDV":
#                 self.chosen_acft_type = 4033
#             self.on_choose_file()
#         elif option == "DFDR 980 I":
#             self.chosen_acft_type = 4022
#             self.on_choose_file()
#         elif option == "4700":
#             self.chosen_acft_type = 403
#             self.on_choose_file()