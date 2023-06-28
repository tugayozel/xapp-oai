import xapp_control_ricbypass
from e2sm_proto import *
from time import sleep

def send_indication_request():
    print("Encoding ric monitoring request")
    
    # external message
    master_mess = RAN_message()
    master_mess.msg_type = RAN_message_type.INDICATION_REQUEST

    # internal message
    inner_mess = RAN_indication_request()
    inner_mess.target_params.extend([RAN_parameter.GNB_ID, RAN_parameter.UE_LIST])

    # assign and serialize
    master_mess.ran_indication_request.CopyFrom(inner_mess)
    buf = master_mess.SerializeToString()
    xapp_control_ricbypass.send_to_socket(buf)

def control_function(ran_ind_resp):
    for ue_info in ran_ind_resp.param_map[1].ue_list.ue_info:
        print(ue_info)

def main():    

    send_indication_request()
    
    while True:
        r_buf = xapp_control_ricbypass.receive_from_socket()
        ran_ind_resp = RAN_indication_response()
        ran_ind_resp.ParseFromString(r_buf)
        print(ran_ind_resp)
        control_function(ran_ind_resp)
        sleep(1)
        send_indication_request()


if __name__ == '__main__':
    main()

