from atj_saf.atj_baseline.systems import atj_system
from atj_saf.atj_baseline.systems import perform_tea



def main():
    atj_system.simulate()
    print("System simulation complete.")
    atj_system.show()

    baseline_tea = perform_tea()


    saf_stream = atj_system.flowsheet.stream['SAF_product']
    saf_density = saf_stream.rho
                                 
    mjsp_usd_kg = baseline_tea.solve_price(saf_stream)
    mjsp_usd_gal = (mjsp_usd_kg*saf_density)/264.172

    print(f'The MJSP is {round((baseline_tea.solve_price(saf_stream)*saf_stream.rho)/264.172,2)} USD/gal')

'''
    print("✅ Simulation complete!")
    system.show()  # Optional: show overall summary
    for u in system.units:
        print(f"\n🔍 {u.ID} output:")
        u.outs[0].show()  # Show outlet stream summary
'''
        

if __name__ == '__main__':
    main()