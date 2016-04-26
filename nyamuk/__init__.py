
# encode unicode string to utf8
#
def utf8encode(unistr):
    if type(unistr) is unicode:
        return unistr.encode('utf8')

    return unistr
