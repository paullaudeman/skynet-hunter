"""Multi-colour pixel T-800 for the terminal ~ downsampled from a reference
image by docs/skull-from-image.py, rendered via the half-block (▀) trick:
foreground = top pixel, background = bottom pixel => two square full-colour
pixels per cell. Regenerate with that script; don't hand-edit COLORS.
"""

from __future__ import annotations

from rich.style import Style
from rich.text import Text

BG = "#0a0706"

COLORS = [
    [None, None, None, None, None, None, None, None, None, None, None, None, '#626462', '#565957', '#454746', '#414342', '#313334', None, None, None, None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, '#3f4141', '#565959', '#5a5c5a', '#525554', '#5d615e', '#70726e', '#6b6d67', '#61635d', '#61625c', '#5e5e59', '#5b5c59', '#585956', '#5a5c5a', '#555859', '#3c3f41', None, None, None, None, None, None, None, None],
    [None, None, None, None, None, '#444545', '#747672', '#6b6c69', '#676763', '#5e5d59', '#5b5a57', '#7c7c76', '#7c7d78', '#767672', '#7f807a', '#787973', '#797974', '#70726b', '#757670', '#757671', '#747570', '#6e706d', '#5f6261', '#3f4246', None, None, None, None, None, None],
    [None, None, None, None, '#5b5e5f', '#888a89', '#757570', '#72706d', '#767673', '#6a6a67', '#42423e', '#4e4e49', '#797976', '#626363', '#5c5e5d', '#575955', '#535552', '#505352', '#5a5c59', '#60625d', '#53544f', '#5e615a', '#666860', '#696b65', '#525658', None, None, None, None, None],
    [None, None, None, '#737678', '#959794', '#85847d', '#83837f', '#838483', '#747674', '#71736f', '#585956', '#393935', '#555756', '#3e4348', '#4d5054', '#5b5d5f', '#494c51', '#4a4c52', '#4b4e51', '#4f5254', '#4d5254', '#535657', '#656764', '#565751', '#5a5953', '#414445', '#272b30', None, None, None],
    [None, None, '#97999a', '#a0a3a5', '#62615d', '#82827e', '#949695', '#767875', '#767775', '#747571', '#5b5a55', '#525351', '#505458', '#4f5255', '#636667', '#585a5c', '#474a52', '#484a51', '#40434c', '#464c58', '#5d646f', '#575d65', '#6f7174', '#7e7c76', '#5e5b54', '#72726c', '#4d5152', '#444549', None, None],
    [None, '#393a39', '#cdcfcf', '#a5a7a3', '#3f403c', '#72726e', '#7b7c78', '#7a7a75', '#6a6966', '#595953', '#696a65', '#6e7070', '#6f7072', '#757676', '#808386', '#656769', '#606162', '#626467', '#56595f', '#575b67', '#575c6a', '#5e636e', '#76797d', '#484743', '#3d3d38', '#6a6862', '#a1a19e', '#707274', None, None],
    [None, '#454646', '#f5f5f5', '#c4c4c1', '#797a76', '#767573', '#716f6b', '#6d6d68', '#626261', '#a2a2a2', '#c1c3c5', '#bec0c5', '#b1b4bb', '#a1a5ac', '#9c9fa6', '#8b8d8f', '#8c8d8f', '#929598', '#989ea2', '#92959c', '#7b7e86', '#636771', '#7f8387', '#343533', '#30302c', '#4c4c47', '#c9cac8', '#cccdce', '#323234', None],
    [None, '#575857', '#fdfdfc', '#f9f9f8', '#cacbcc', '#9b9da0', '#959698', '#b0b1b4', '#cecfd2', '#f6f7f9', '#e3e6ea', '#dee2ea', '#d2d7e0', '#c2c6cf', '#b1b5ba', '#9fa1a3', '#afb3b7', '#cfd3d7', '#e9edf0', '#f3f5f8', '#ececed', '#d0d1d3', '#a6a7a6', None, None, '#31322f', '#dbdbd9', '#f5f5f6', '#4e4e50', None],
    [None, '#99999b', '#fefefe', '#ffffff', '#d8d9dd', '#b9bac0', '#e7e8e9', '#fafafb', '#ffffff', '#e6e7eb', '#b1b4b9', '#c3c5c8', '#d4d5d9', '#c2c4cb', '#babec2', '#c9ccce', '#ccd2d6', '#f3f5f5', '#fbfbf9', '#f8f9f8', '#ffffff', '#ffffff', '#eaeae8', '#545551', None, '#373834', '#eeedeb', '#f1f0ef', '#6b6d71', None],
    ['#54565a', '#eceef3', '#fcfcfc', '#ffffff', '#cccccf', '#e1e1e4', '#ffffff', '#fbfbfb', '#fdfdfd', '#cacbd0', '#b3b5b8', '#bdbcb8', '#a0a2a2', '#979ba2', '#a3a9b1', '#c2c7ca', '#adb1b5', '#ccccca', '#a7a69e', '#c6c8c7', '#fcfdfd', '#fdfdfd', '#ffffff', '#f1f1ef', '#9f9e9a', '#9e9992', '#fefefe', '#f3f3f0', '#a3a3a4', None],
    ['#555657', '#e7e8e7', '#fffffe', '#fffefe', '#c1c3c5', '#dee0e2', '#fefefe', '#fdfdfd', '#ffffff', '#d2d3d7', '#aeb0b1', '#acaba1', '#7d7f7a', '#8a8d92', '#9ea4ad', '#9ba1a7', '#93969c', '#9e9f9e', '#7e7d73', '#bdbdbb', '#e8eaec', '#ffffff', '#fefefe', '#ffffff', '#d8d9d6', '#cec7c3', '#ffffff', '#f7f7f6', '#e5e3e0', '#4a4a47'],
    ['#5b5b58', '#c0bfbd', '#fbfbfb', '#fafaf9', '#b7b9bb', '#cfd1d3', '#ffffff', '#fefefd', '#ededed', '#a1a3a8', '#bec3c8', '#b8b8b1', '#66655c', '#9fa1a0', '#9da1a3', '#8b8f94', '#a3a6ab', '#9b9b97', '#838279', '#d3d4d3', '#dfe3e7', '#fbfbfc', '#ffffff', '#fefefe', '#cfd0ce', '#c2bbb8', '#fdfdfd', '#dcdcda', '#d5d4cf', '#40403c'],
    ['#515353', '#9fa09c', '#c8c8c7', '#e2e3e5', '#c1c2c4', '#cacbcd', '#ffffff', '#fefefe', '#c1c2c5', '#87888f', '#a6abb2', '#c1c2bd', '#56554c', '#757671', '#6c6f6e', '#7b7b80', '#989c9d', '#8a8b84', '#8e8c84', '#cdcecf', '#cacfd3', '#f6f7f8', '#ffffff', '#fffeff', '#dee0dd', '#c0bab8', '#f4f4f4', '#a3a29f', '#adaca3', '#343330'],
    [None, '#82837f', '#93938e', '#c2c4c5', '#d3d4d7', '#c8cacb', '#ffffff', '#e5e6e8', '#8e9198', '#72747a', '#a5aab1', '#cacdc9', '#595950', None, '#434441', '#7b7c7b', '#5b5b58', '#42433e', '#898883', '#bec1c2', '#a7acb1', '#e4e6e8', '#ffffff', '#fefefe', '#eef0ef', '#c2bdb8', '#e5e3e3', '#b2b1ae', '#94928a', None],
    [None, '#60615d', '#c9c9c5', '#e8e9e7', '#cfd2d7', '#c7c8ca', '#ffffff', '#d4d6d9', '#777b83', '#71757a', '#8b9198', '#c7c9c7', '#74746c', None, None, '#54564f', None, None, '#8e8f8c', '#bbbfc1', '#888d91', '#9c9fa8', '#c9cccf', '#ffffff', '#f9f9f9', '#bbb7b2', '#d5d1ce', '#c2c1c1', '#93918b', None],
    [None, '#6d6c69', '#dbdad7', '#f7f6f6', '#cacdd1', '#d2d5d5', '#fbfbfa', '#eff0f0', '#7b8088', '#6c6f77', '#85898e', '#bfc3c6', '#a6a6a0', None, '#32322e', '#5c5c56', None, '#2d2d2a', '#a9aaa8', '#909499', '#7b7f87', '#a0a5b2', '#8a8f94', '#dddfdd', '#f4f4f2', '#c4c3c1', '#c3beba', '#c4c5c7', '#e0e0de', '#2e2e2d'],
    [None, '#b9b9b7', '#f7f8f7', '#f8f8f8', '#c9ccd0', '#e7e8e7', '#fffefc', '#c7c9cb', '#8c9197', '#9b9d9e', '#747577', '#96999e', '#babbb6', '#6e6d69', '#73726d', '#82837f', '#888985', '#83827f', '#989b9a', '#979a9e', '#a3a4aa', '#9ea1a3', '#adb1b4', '#f0f0ef', '#ffffff', '#f4f4f5', '#bcb7b4', '#cccbcd', '#b7b9be', '#2f2f2f'],
    [None, '#888985', '#e4e6e5', '#f0f1f3', '#b9bcc2', '#dddee1', '#bfc1c5', '#a1a5a9', '#aeb0b1', '#9b9d9f', '#787a7b', '#8e8f91', '#989892', '#595853', '#555650', '#525450', '#7b7b76', '#757670', '#969896', '#9a9c9d', '#9c9fa2', '#cacdcd', '#adb1b4', '#c4c6c7', '#f0f0f0', '#e9ebea', '#b4b3af', '#bcb4af', '#aaa8a6', '#2e2d2b'],
    [None, '#777876', '#caccca', '#d6d7d7', '#9d9e9e', '#727575', '#5c5c5c', '#636362', '#6f6f6b', '#797979', '#7f807f', '#868786', '#94948c', '#5c5b54', '#51514e', '#454746', '#646662', '#6f706c', '#7d7f7d', '#767774', '#4b4e4c', '#61605c', '#636461', '#7a7e7a', '#9c9c9a', '#8d8f8b', '#81827f', '#979189', '#9f968c', '#56514c'],
    ['#292b2c', '#5f605e', '#878885', '#898986', '#6f6e6b', '#6f6b68', '#716b68', '#726a66', '#554a47', '#3f3b3a', '#3c3e3e', '#404241', '#686864', '#6a695f', '#4a4b48', '#383a38', '#575954', '#5a5a55', '#4c4e4c', '#484a46', '#4e4d49', '#3a3a3a', '#4a403f', '#5e4f4e', '#5f5a5a', '#474547', '#363537', '#3c3a37', '#948e85', '#8c8785'],
    [None, '#838381', '#807f7c', None, None, None, None, '#86442a', '#a96635', '#77402f', '#4a3b3a', '#343131', '#3e3e3f', '#6b6c67', '#636661', '#3f413d', '#515450', '#747671', '#4c4c4d', '#474647', '#585452', '#583632', '#a16b55', '#a06853', None, None, None, None, '#b3b0aa', '#b9b7b8'],
    ['#313431', '#fcfdfb', '#cccbc8', None, None, None, '#4f2d24', '#ccab99', '#ebcfc3', '#874d34', None, None, None, '#403b39', '#625e5b', '#4e4f4d', '#5a5652', '#49433e', None, None, None, '#694227', '#fcf8ad', '#fffdc0', '#8c694c', None, None, '#494642', '#c2c0c2', '#9fa0a4'],
    [None, '#e7e9e6', '#e2e3e1', '#3a3634', None, None, '#896558', '#f1e2c9', '#fffffd', '#b38b69', None, None, None, '#6d3e35', '#a5867d', '#d5dcdb', '#d0c5c0', '#854232', None, None, None, '#5d4539', '#e4ce68', '#e9db7c', '#675244', None, None, '#3f3a39', '#bdbcbf', '#6f6e6f'],
    [None, '#d1d2cf', '#ffffff', '#5e5a56', None, None, None, '#9c7762', '#bf936c', '#664438', None, None, '#413231', '#b16e5b', '#ceaa94', '#bdc5c7', '#dad6d1', '#c47a5d', '#855f54', None, None, None, '#41231b', '#41281f', None, '#46443e', None, '#433f3e', '#c0b7ab', '#68635e'],
    [None, '#bcbebd', '#e5e7e7', '#acaca9', '#57534d', '#6d6a65', '#332b27', None, None, None, None, '#47413f', '#8b7c78', '#b2968c', '#e5d4c7', '#454746', '#8f8e8a', '#cbb6a8', '#867972', '#676561', '#514d4a', '#433a37', None, None, '#595652', '#494947', '#505051', '#8f8b87', '#a79b89', '#665e53'],
    [None, '#8e8f8d', '#bcbeb8', '#979794', '#797979', '#767576', '#676766', '#524c48', '#503f3a', '#584745', '#575251', '#5b5a57', '#8f8c88', '#928d89', '#bfbebb', None, '#555555', '#c0beba', '#948b84', '#83807a', '#515251', '#585554', '#5a5452', '#595655', '#61615e', '#444444', '#777674', '#8a8985', '#83796b', '#4d463b'],
    [None, '#3c3d3b', '#adafa9', '#8e8e89', '#8b8c89', '#6c6d6c', '#3e3f3f', '#42423f', '#404241', '#393b3a', None, '#686865', '#979491', '#74726e', '#646561', None, None, '#797873', '#77746a', '#968c7e', '#5d5e57', '#313334', '#2d3032', '#2e3131', '#42433e', '#474742', '#393a38', '#80807d', '#918473', None],
    [None, '#333332', '#9fa09c', '#686a69', '#525451', None, '#2f3232', '#2c2e2d', '#2f3235', '#363739', '#464745', '#b5b6af', '#61605c', '#44443f', '#373737', None, None, '#333532', '#464640', '#8f8b82', '#8b8a85', '#80837f', '#515455', '#303538', '#35393b', '#363838', '#757677', '#444644', '#393631', None],
    [None, None, '#939490', '#7a7d7b', '#88898a', '#666868', '#303337', '#282b2f', '#2e3234', None, '#363736', '#a4a59f', '#8b8b86', '#3e3f3a', None, None, None, None, '#5c5d58', '#898680', '#30302e', '#323331', None, None, None, '#45494c', '#444547', None, None, None],
    [None, None, '#2f2f2c', '#7a7c7a', '#3a3e41', '#4e5050', '#2f3131', None, None, None, '#484843', '#70716c', '#aaa8a4', '#3e413b', None, '#464745', '#2f312e', None, '#666763', '#796e61', '#585952', '#6a6a67', None, None, None, None, '#40403d', None, None, None],
    [None, None, None, '#52534d', '#4d4f4a', None, None, None, None, '#60625e', '#3e3e3b', '#939492', '#8c8e8d', '#7f817e', '#696a67', '#4e514f', '#595b56', '#747672', '#757772', '#7c7770', '#393934', '#494a46', '#3b3736', None, None, '#404040', '#666661', None, None, None],
    [None, None, None, '#40413d', '#3d3e3a', '#696a68', None, None, '#4c4d50', '#2d2f2e', None, '#c7c7c7', '#d9dbdb', '#747877', '#787a78', '#2e3131', '#5c5e5a', '#6b6d68', '#b0b2af', '#d8d6d3', '#5a5752', None, '#3d3e3b', '#363735', None, '#686868', '#51504c', None, None, None],
    [None, None, None, '#42433e', '#2c2c29', '#595a56', '#404340', '#525352', None, None, '#717473', '#dfdfdd', '#d2d3d4', '#6f7373', '#767978', '#585a58', '#666765', '#a4a59f', '#f5f6f4', '#f3f2f0', '#a29e98', '#80827e', None, '#635f58', '#696863', '#6a6a67', '#54534f', None, None, None],
    [None, None, None, '#666863', '#3e3e3a', '#65665e', '#656864', '#2b2c2a', None, '#898c8e', '#9c9f9f', '#a2a4a2', '#848889', '#6f7371', '#878b8b', '#6a6c6c', '#808384', '#b9bbb9', '#b7b9b7', '#d1d4d3', '#9b968e', '#b0aba5', '#504d46', None, '#6c6a65', '#8c8a86', '#76736d', '#423c35', None, None],
    [None, None, None, '#949590', '#807f76', '#8d8b82', '#83837f', None, None, '#54524e', '#828077', '#444543', '#787a7a', '#575a5b', '#2c2f33', None, '#323638', '#565859', '#838581', '#80817f', '#635e56', '#908574', '#584e3e', '#312c22', '#66645e', '#a09f9a', '#938e87', '#514941', None, None],
    [None, None, None, '#9fa19b', '#a6a69f', '#92918a', '#83847f', '#423d32', None, '#413a2f', '#af9e7e', '#877659', '#786b53', '#625541', '#564b37', '#524631', '#54482f', '#6e6349', '#86795c', '#786647', '#a0916d', '#bba984', '#625746', '#594e3f', '#45403a', '#666562', '#8c8980', '#433c37', None, None],
    [None, None, None, '#727470', '#9f9f97', '#6e6e65', '#6c6d67', '#7c7b75', '#666762', '#504b41', '#af9e7f', '#c3b591', '#b09f79', '#a99973', '#b4a57c', '#beaf85', '#ad9b72', '#bcaf85', '#ad9c70', '#a69164', '#ae9c71', '#907d57', '#756f63', '#88867d', '#302f2b', '#3b3a39', '#7f7a73', None, None, None],
    [None, None, None, None, '#a7a89f', '#5e5f58', '#555652', '#6f706b', '#9fa09b', '#afada4', '#897d6a', '#9b8c6a', '#94815a', '#95825e', '#937f58', '#917e56', '#8a744e', '#907f59', '#927e5a', '#88744c', '#816b44', '#827359', '#969189', '#73756f', '#2b2b28', '#4b4a43', '#5a5652', None, None, None],
    [None, None, None, None, '#61605b', '#85857e', '#5a5c58', '#3f413e', '#545552', '#a2a4a0', '#cdccc5', '#938c80', '#908571', '#8b7c64', '#7b6952', '#76644b', '#7c694b', '#7b694b', '#7c6a4f', '#85755c', '#90836e', '#928c85', '#4a4b48', '#4e504c', '#3d3d3a', '#64625d', None, None, None, None],
    [None, None, None, None, None, '#817f79', '#7d7d77', '#8b8b85', '#6a6b69', '#60615a', '#82847a', '#939592', '#aeaeac', '#6d6d69', '#5e5d57', '#605d58', '#57554d', '#5b5952', '#868680', '#a9aba7', '#666561', None, '#3b3c39', '#494944', '#5e5d57', '#44433e', None, None, None, None],
    [None, None, None, None, None, '#393a37', '#909087', '#b9bbb5', '#9b9c98', '#6d6d67', None, '#383a37', '#868882', None, None, None, None, None, '#464946', '#787b75', None, None, '#3e403d', '#6d6c69', '#726e69', None, None, None, None, None],
    [None, None, None, None, None, None, None, '#b1b4ae', '#a2a49f', '#a3a49d', '#656661', None, '#3a3c39', '#3b3c37', None, None, None, None, '#393b39', '#3a3c3a', None, '#4b4b47', '#52504b', '#3b3b36', None, None, None, None, None, None],
    [None, None, None, None, None, None, None, '#575756', '#d8dad5', '#a6a9a3', None, None, '#2b2d2b', '#4a4c47', '#363832', '#3a3c38', '#3d3e3c', '#474740', '#4a4c45', None, None, None, '#78746d', '#34322f', None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, '#71716d', '#898b81', None, '#292b2a', '#474843', '#979995', '#9a9c96', '#73746c', '#63645c', '#7d7f75', '#8d8e89', '#31332f', None, '#31322e', '#5a5854', None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, '#42423c', '#808077', '#9d9c97', '#d2d1cf', '#cbcdcd', '#a4a9a7', '#c5cbc7', '#cad0cc', '#c4c9c9', '#e2e5e5', '#96958e', '#3e3e39', '#6d6b63', None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None, '#40413b', '#92948d', '#aeb0ae', '#676a6b', '#595b5b', '#707476', '#8e9293', '#929698', '#777b7e', '#a4a6a1', '#67635b', '#2f2d2a', None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None, None, None, '#3d3f3f', '#343737', None, None, None, None, '#333635', '#4b4e4f', None, None, None, None, None, None, None, None, None, None],
]


def skull_text() -> Text:
    t = Text(justify="center")
    rows = COLORS
    width = len(rows[0]) if rows else 0
    for r in range(0, len(rows), 2):
        top = rows[r]
        bot = rows[r + 1] if r + 1 < len(rows) else [None] * width
        for c in range(width):
            tc = top[c] or BG
            bc = bot[c] or BG
            t.append("▀", style=Style(color=tc, bgcolor=bc))
        t.append("\n")
    return t
