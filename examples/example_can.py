import time
from pysilkit import SilKit, SilKitParticipant, CanMessage

if __name__ == "__main__":
    s = SilKit("Test1", "Test2")
    p = SilKitParticipant("Test1")
    p.add_can_controller("Test1_CAN")
    p2 = SilKitParticipant("Test2")
    p2.add_can_controller("Test2_CAN")
    p.can(0).start()
    p2.can(0).start()
    msg = CanMessage(
        0x700,
        *(1,2,3,4,5,6,7,8),
    )
    print(msg)
    p.can(0).send(msg)
    print("SENT", p.can(0).wait_tx_ack(msg))
    d = p2.can(0).recv()
    print("RECV", d)
    msg = CanMessage(
        0x701,
        *(1,2,3,4,5,6,7,9),
    )
    p.can(0).send(msg)
    time.sleep(0.1)#Wait for ack
    d = p2.can(0).recv()
    print("SENT", p.can(0).recv())
    print("RECV", d)
    msg = CanMessage(
        0x702,
        *(1,2,3,4,5,6,7,10),
    )
    p.can(0).send(msg)
    time.sleep(0.1)#Wait for ack
    d = p2.can(0).recv()
    print("SENT", p.can(0).recv())
    print("RECV", d)
    msg = CanMessage(
        0x703,
        *(1,2,3,4,5,6,7,11),
    )
    p.can(0).send(msg)
    time.sleep(0.1)#Wait for ack
    d = p2.can(0).recv()
    print("SENT", p.can(0).recv())
    print("RECV", d)
    p.can(0).sleep()
    p.can(0).reset()
    p.can(0).stop()
