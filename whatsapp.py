"""Offline, deterministic WhatsApp conversation mock; never sends messages/payments."""
def initial(action, amount, discount=20, language='hinglish'):
    if action == 'Ship after confirmation':
        return (f'Namaste! Aapka COD order Rs {amount} dispatch ke liye ready hai. Confirm karein: YES / NO.' if language == 'hinglish' else f'Your COD order of Rs {amount} is ready. Reply YES to confirm or NO to request cancellation.')
    if action == 'Nudge to prepaid':
        return (f'Namaste! Aapka COD order Rs {amount} hai. Online payment par Rs {discount} bachayein. PAY / COD / NO reply karein.' if language == 'hinglish' else f'Your COD order is Rs {amount}. Pay online and save Rs {discount}. Reply PAY for a payment link, COD to keep COD, or NO to request cancellation.')
    return 'No message required.'

def transition(action, message, state='awaiting_reply'):
    """Return a mock state and response. A payment link/payment webhook is never simulated as real."""
    if state in {'confirmed', 'cancel_requested', 'manual_review', 'prepaid_verified'}:
        return state, 'This flow is closed. Start a new simulation for another response.'
    m = str(message).strip().casefold()
    if not m:
        return state, 'Awaiting customer reply.'
    if m in {'no','n','2','cancel','nahi','nahin','cancel order'}:
        return 'cancel_requested', 'Cancellation requested: hold order and ask staff to verify before cancelling.'
    if action == 'Ship after confirmation':
        if m in {'yes','y','1','haan','ha','confirm','yes confirm','confirm order'}:
            return 'confirmed', 'CONFIRMED: order may be released for shipping.'
        if '?' in m or any(w in m.split() for w in ('why','when','where','how','delivery','address','discount','price','kab','kyu','kaise')):
            return 'needs_clarification', 'Thanks for your question. This offline mock cannot verify delivery or account details. A support agent will help. Please reply YES to confirm or NO to request cancellation.'
        return 'needs_clarification', 'Sorry, I could not understand. Please reply YES to confirm or NO to request cancellation.'
    if action == 'Nudge to prepaid':
        if m in {'pay','prepaid','online','pay online'}:
            return 'awaiting_payment', 'DEMO ONLY: a secure expiring payment link would be sent. Do not mark prepaid until a verified payment webhook arrives.'
        if m in {'cod','cash','cash on delivery'}:
            return 'awaiting_cod_confirmation', 'COD selected. Please reply YES to confirm the COD order or NO to request cancellation.'
        if state == 'awaiting_cod_confirmation' and m in {'yes','y','haan','confirm'}:
            return 'confirmed', 'CONFIRMED: customer chose COD and confirmed the order.'
        if state == 'awaiting_payment' and m in {'paid','done','payment done'}:
            return 'awaiting_payment', 'Payment claim received. Await verified payment webhook; do not release based on a chat message.'
        return 'needs_clarification', 'Please reply PAY for online payment, COD to keep cash on delivery, or NO to request cancellation.'
    return state, 'No active flow.'

def reply(action, message):
    return transition(action,message)[1]

def timeout(hours_elapsed, config):
    if hours_elapsed >= config['confirmation_hours']:
        return 'Hold and queue for manual review; never silently ship or cancel.'
    if hours_elapsed >= config['reminder_hours']:
        return 'Send one reminder (if not already sent).'
    return 'Await response.'
