import re

def format_string(string):
    if type(string) != unicode:
        string = unicode(string, 'UTF-8')
    new_string = convert_non_character_to_dash(string)
    new_string = remove_consecutive_dashes(new_string)
    # removing leading dashes, if any
    if new_string[0] == '-':
        new_string = new_string[1:]
    # removing trailing dashes, if any
    if new_string[len(new_string)-1] == '-':
        new_string = new_string[0:-1]
    return new_string.lower()

def remove_consecutive_dashes(title):
    reduced_title = re.sub(r'(\-)\1+', r'\1', title)
    return reduced_title

def convert_non_character_to_dash(title):
    title_unicode_trans = TitleUnicodeTranslate()
    return title.translate(title_unicode_trans)

class TitleUnicodeTranslate(dict):
    def __missing__(self,item):
        uni = unichr(item)
        res = u"-"
        if uni.isupper() or uni.islower() or uni.isdigit():
            res = uni
        if uni == u"'":
            res = u""
        self[item] = res
        return res