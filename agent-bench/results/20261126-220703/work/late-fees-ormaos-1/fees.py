"""The late fee of one invoice for one night."""


def days_late(invoice, day):
    return (day - invoice.due_on).days


def is_chargeable(invoice, day, settings):
    """Overdue past the grace period of its plan, not paid, not disputed."""
    if invoice.paid_on is not None and invoice.paid_on <= day:
        return False
    if invoice.disputed:
        return False
    grace = settings.grace_days.get(invoice.plan, settings.grace_days["standard"])
    return days_late(invoice, day) > grace


def fee_for(invoice, charged_so_far, settings):
    """Cents to charge tonight: the daily fee, up to the cap of the invoice."""
    daily = invoice.amount_cents * settings.daily_basis_points // 10000
    daily = max(daily, settings.minimum_cents)
    cap = invoice.amount_cents * settings.cap_percent // 100
    return max(0, min(daily, cap - charged_so_far))
