from lignin_saf.ligsaf_system import ligsaf_system


def main():
    ligsaf_system.simulate()
    print("System simulation complete.")
    ligsaf_system.show()



if __name__ == '__main__':
    main()
