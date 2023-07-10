import xapp_control_ricbypass
from e2sm_proto import *
from time import sleep

def send_indication_request():
    print("Sending indication request")
    
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
    print("\n")

def send_control_request(labeled_ues):

    # ue list message 
    ue_list_message = ue_list_m()
    ue_list_message.connected_ues = 1 # this will not be processed by the gnb, it can be anything
    counter = 0
    for ue in labeled_ues.values():
        if(ue["label"]):
            # ue info message
            ue_info_message = ue_info_m()
            ue_info_message.rnti = ue["rnti"]
            if(ue["prop_1"] == RAN_mcs_type.SIXTEEN_QAM):
                ue_info_message.prop_1 = RAN_mcs_type.SIXTYFOUR_QAM
                print(f"For RNTI = {ue_info_message.rnti}, the MCS has been changed from 16QAM to 64QAM")
            else:
                ue_info_message.prop_1 = RAN_mcs_type.SIXTEEN_QAM
                print(f"For RNTI = {ue_info_message.rnti}, the MCS has been changed from 64QAM to 16QAM")

            # put info message into repeated field of ue list message
            ue_list_message.ue_info.extend([ue_info_message])
            counter += 1
    print(f"Number of UEs with MCS changed: {counter}")
    print("\n")

    print("Sending control message")
    master_mess = RAN_message()
    master_mess.msg_type = RAN_message_type.CONTROL
    inner_mess = RAN_control_request()
    
    # ue list map entry
    ue_list_control_element = RAN_param_map_entry()
    ue_list_control_element.key = RAN_parameter.UE_LIST
    
    

    # put ue_list_message into the value of the control map entry
    ue_list_control_element.ue_list.CopyFrom(ue_list_message)

    # finalize and send
    inner_mess.target_param_map.extend([ue_list_control_element])
    master_mess.ran_control_request.CopyFrom(inner_mess)
    #print(master_mess)
    buf = master_mess.SerializeToString()
    xapp_control_ricbypass.send_to_socket(buf)


def control_function(ran_ind_resp):
    labeled_ues = {}
    change = False
    print("Employing Control Function\n")

    for ue_info in ran_ind_resp.param_map[1].ue_list.ue_info:
        rnti = ue_info.rnti
        meas_type_1 = ue_info.meas_type_1
        prop_1 = ue_info.prop_1
        
        if prop_1 == RAN_mcs_type.SIXTEEN_QAM:
            label = meas_type_1 < 0.02653260982614602
            change = label
        elif prop_1 == RAN_mcs_type.SIXTYFOUR_QAM:
            label = meas_type_1 > 0.04189230318126343
            change = label
        else:
            label = None
        
        labeled_ues[rnti] = {
            'rnti': rnti,
            'meas_type_1': meas_type_1,
            'prop_1': prop_1,
            'label': label
        }
    if(change):
        send_control_request(labeled_ues)
    else:
        print("No UEs found to be changed\n")

def main():    

    send_indication_request()
    
    while True:
        r_buf = xapp_control_ricbypass.receive_from_socket()
        ran_ind_resp = RAN_indication_response()
        ran_ind_resp.ParseFromString(r_buf)
        print(ran_ind_resp)
        control_function(ran_ind_resp)
        sleep(4)
        send_indication_request()


if __name__ == '__main__':
    main()

