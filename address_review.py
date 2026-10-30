"""Deterministic address checks. No LLM is called; optional LLM work is documented in README."""
import re
FAKE={'test','asdf','abc','xyz','na','none','qwerty','aaaa','dummy'}
LANDMARKS=('near','opposite','beside','behind','chowk','mandir','bank','road','street','gali','nagar','sector','saamne','pass','paas','left','right','house','flat','plot','h.no')
def review(name,address,pincode):
    n=str(name).strip().lower(); a=str(address).strip(); pin=str(pincode).strip().removesuffix('.0')
    flags=[]
    if n in FAKE or len(n)<3 or bool(re.fullmatch(r'(.)\1{3,}',n)):flags.append('Suspicious customer name; verify manually')
    if not re.fullmatch(r'[1-9][0-9]{5}',pin):flags.append('Pincode must be six digits and cannot begin with zero')
    if len(a)<15 or len(a.split())<3:flags.append('Address may be incomplete; request landmark or house details')
    return {'flags':flags,'landmark_detected':any(x in a.lower() for x in LANDMARKS),'method':'deterministic checks; no LLM used'}
