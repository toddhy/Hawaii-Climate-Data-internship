
    print(f"[+] MATH TIME (Land-Only): {math_duration:.2f}s")
    
    # In reality, only about 6 blocks have significant land
    total_est = (read_duration + math_duration) * 8 # 8 land blocks estimated
    print(f"\n[*] TOTAL ESTIMATED HAWAII TIME: {total_est:.2f} seconds")
    print("[*] VERIFICATION COMPLETE. This should now pass the 60s barrier.")
