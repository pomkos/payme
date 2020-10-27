def venmo_requester(my_dic, total, tax=0, tip=0, misc_fees=0):
    """
    Returns lump sums to request using venmo
    
    input
    -----
    my_dic: dict
        Dictionary of name:[list of prices]
    total: float
        Total shown on receipt, charged to your card
    tax: float
        Tax applied in dollars, not percent
    tip: float
        Amount tipped in dollars, not percent
    misc_fees: float
        Sum of all other fees not accounted for, like delivery fee, etc
        
    output
    -----
    request: dict
        Dictionary of name:amount, indicating how much to charge each person
    """
    precheck_sum = 0
    for key in my_dic.keys():
        precheck_sum += sum(my_dic[key])
    
    precheck_sum = round(precheck_sum+tax+tip+misc_fees,2)
    if total != precheck_sum:
        return f"You provided {total} as the total, but I calculated {precheck_sum}"
    else:
        num_ppl = len(my_dic.keys())
        tip_perc = tip/total
        tax_perc = tax/total
        fee_part = misc_fees/num_ppl
        request = {}
        rounded_sum = 0
        for key in my_dic.keys():        
            my_list = my_dic[key]

            my_total = sum(my_list)
            tax_part = tax_perc * my_total
            tip_part = tip_perc * my_total

            person_total = round(my_total + tax_part + fee_part + tip_part,2)
            rounded_sum += person_total
            request[key] = person_total
    
        if rounded_sum < total:
            print(f"* After rounding the calculated sum is {rounded_sum}, but the total charged to your credit card was {total}")
            rounding_error = round((total - rounded_sum)/num_ppl,2)
            for key in request.keys():
                request[key] += rounding_error
            print(f"* Rounding error found and adjusted for by adding {rounding_error} to each person.")
            
            new_total = 0
            for key in request.keys():
                new_total += request[key]
            print(f"* Confirmed {new_total} accounted for")
        elif rounded_sum > total:
            return (f"Uh oh! My calculated venmo charge sum is {rounded_sum} but the receipt total was {total}")
        else:
            print(f"The venmo charge sum is same as the receipt total, no rounding correction needed")
        print("___________________________")
        print('')
        print('Venmo Requests:')
        for key in request.keys():
            print(f'{key}: ${round(request[key],2)}')
        print("___________________________")
        print('')
        print('Venmo Comments:')
        for key in request.keys():
            print(f'* {key}: food was ${round(sum(my_dic[key]),2)}, tip was {round(tip_perc*100,2)}%, tax was {round(tax_perc*100,2)}%, fees were ${round(fee_part,2)}')
            
receipt = str(input("Enter the name followed by the itemized food costs: "))
total = float(input("Enter the amount charged to your credit card, including the tip: "))
tip = float(input("Enter the amount tipped, in dollars not percentage: "))
tax = float(input("Enter the amount taxed, in dollars not percentage: "))
fees = float(input("Enter the total misc fees: "))

venmo_requester(receipt, total=total, tax=tax, tip=tip, misc_fees=misc_fees)