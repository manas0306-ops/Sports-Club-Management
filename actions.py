from services import *
ROLES={
    "register":None,"login":None,"lead":None,"logout":["member","desk","bar","shop","physio"],
    "upgrade":["member","desk"],"book":["member","desk"],"cancel":["member","desk"],
    "walkin":["desk"],"lead_stage":["desk"],"trial":["desk"],"order":["shop","member"],
    "fulfil":["shop"],"adjust":["shop"],"open_shift":["bar"],"close_shift":["bar"],
    "tab":["bar"],"batch":["bar"],"settle":["bar"],"ticket":["bar"],
    "appointment":["member"],"complete":["physio"],"add_user":[],"edit_user":[],"archive":[],
    "invoice":[],"schedule":[],"leave":["bar","desk","physio","shop"],"decide":[],"payroll":[]
}
