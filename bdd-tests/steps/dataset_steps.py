from behave import given


@given('the debtor {debtor_name} has fiscal code {debtor_fc}')
def step_citizen_fc_exact_or_random(context, debtor_name, debtor_fc, random_fiscal_code):
    if debtor_fc == 'random':
        debtor_fc = random_fiscal_code

    context.latest_citizen_fc = debtor_fc

    try:
        context.debtor_fc[debtor_name] = debtor_fc
    except AttributeError:
        context.debtor_fc = {debtor_name: debtor_fc}
