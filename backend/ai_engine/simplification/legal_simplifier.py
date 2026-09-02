REPL={"hereinafter":"from now on","notwithstanding":"despite","pursuant to":"under","terminate":"end","remuneration":"payment"}
def simplify(text):
    for a,b in REPL.items(): text=text.replace(a,b).replace(a.title(),b)
    return text
