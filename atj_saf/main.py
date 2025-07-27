from atj_saf.atj_baseline.systems import atj_system
from atj_saf.atj_baseline.systems import perform_tea



def main():
    atj_system.simulate()
    print("System simulation complete.")
    atj_system.show()

    baseline_tea = perform_tea()
    print(f"\n: {baseline_tea.NPV}")


'''
    print("✅ Simulation complete!")
    system.show()  # Optional: show overall summary
    for u in system.units:
        print(f"\n🔍 {u.ID} output:")
        u.outs[0].show()  # Show outlet stream summary
'''
        

if __name__ == '__main__':
    main()