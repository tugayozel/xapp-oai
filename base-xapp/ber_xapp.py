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

def send_control_request(rnti, mcs_type):
    print("Sending control message")
    master_mess = RAN_message()
    master_mess.msg_type = RAN_message_type.CONTROL
    inner_mess = RAN_control_request()
    
    # ue list map entry
    ue_list_control_element = RAN_param_map_entry()
    ue_list_control_element.key = RAN_parameter.UE_LIST
    
    # ue list message 
    ue_list_message = ue_list_m()
    ue_list_message.connected_ues = 1 # this will not be processed by the gnb, it can be anything

    # ue info message
    ue_info_message = ue_info_m()
    ue_info_message.rnti = rnti
    ue_info_message.prop_1 = mcs_type
    #ue_info_message.prop_2 = prop_2

    # put info message into repeated field of ue list message
    ue_list_message.ue_info.extend([ue_info_message])

    # put ue_list_message into the value of the control map entry
    ue_list_control_element.ue_list.CopyFrom(ue_list_message)

    # finalize and send
    inner_mess.target_param_map.extend([ue_list_control_element])
    master_mess.ran_control_request.CopyFrom(inner_mess)
    print(master_mess)
    buf = master_mess.SerializeToString()
    xapp_control_ricbypass.send_to_socket(buf)


def control_function(ran_ind_resp):
    labeled_ues = {}
    
    for ue_info in ran_ind_resp.param_map[1].ue_list.ue_info:
        rnti = ue_info.rnti
        meas_type_1 = ue_info.meas_type_1
        prop_1 = ue_info.prop_1
        
        if prop_1 == RAN_mcs_type.SIXTEEN_QAM:
            label = meas_type_1 < 0.02653260982614602
        elif prop_1 == RAN_mcs_type.SIXTYFOUR_QAM:
            label = meas_type_1 > 0.04189230318126343
        else:
            label = None
        
        labeled_ues[rnti] = {
            'rnti': rnti,
            'meas_type_1': meas_type_1,
            'prop_1': prop_1,
            'label': label
        }
    
    return labeled_ues

def main():    

    send_indication_request()
    
    while True:
        r_buf = xapp_control_ricbypass.receive_from_socket()
        ran_ind_resp = RAN_indication_response()
        ran_ind_resp.ParseFromString(r_buf)
        print(ran_ind_resp)
        print(control_function(ran_ind_resp))
        sleep(4)
        send_indication_request()


if __name__ == '__main__':
    main()

