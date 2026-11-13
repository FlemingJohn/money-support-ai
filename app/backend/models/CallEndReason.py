from typing import Literal

CallEndReason = Literal["callerHungUp", "agentEndedCall", "handedOff", "silenceTimeout", "timeLimit", "error"]
