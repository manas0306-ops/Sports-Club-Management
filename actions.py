from services import *
ROLES={
    "register":None,"login":None,"lead":None,"logout":["member","desk","bar","shop","physio"],
    "upgrade":["member","desk"],"book":["member","desk"],"cancel":["member","desk"],
    "walkin":["desk"],"lead_stage":["desk"],"trial":["desk"],"order":["shop","bar","member"],
    "fulfil":["shop"],"adjust":["shop"],"update_order_status":["shop","desk"],
    "open_shift":["bar"],"close_shift":["bar"],
    "tab":["bar"],"batch":["bar"],"settle":["bar"],"ticket":["bar"],
    "appointment":["member"],"complete":["physio"],"add_user":[],"edit_user":[],"archive":[],
    "invoice":[],"schedule":[],"leave":["bar","desk","physio","shop"],"decide":[],"payroll":[],
    "verify_payment":["desk"],"approve_booking":["desk"],
    "reject_payment":["desk"],"reject_booking":["desk"],
    "confirm_all_bookings":["desk"],"reject_all_bookings":["desk"],
    "add_product":["shop","desk","bar"],"edit_product":["shop","desk","bar"],"delete_product":["shop","desk","bar"],"remove_product":["shop","desk","bar"],
    "block_court":["desk"],"unblock_court":["desk"],
    "update_profile":["member","desk","bar","shop","physio"],"change_password":["member","desk","bar","shop","physio"]
}
