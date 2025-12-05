from behave import given


@given('the debtor {debtor_name} has fiscal code {debtor_fc}')
def step_citizen_fc_exact_or_random(context, debtor_name, debtor_fc):
    if debtor_fc == 'random':
        debtor_fc = context.fake_fc()

    context.latest_citizen_fc = debtor_fc

    if not hasattr(context, 'debtor_fc') or context.debtor_fc is None:
        context.debtor_fc = {}

    context.debtor_fc[debtor_name] = debtor_fc
