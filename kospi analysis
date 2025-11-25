import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

def run_policy_simulation():
    """
    Runs a simplified simulation of the KOSPI Value-Up Policy.

    This is not an econometric forecast but an illustration of the potential
    impact of re-rating (PBR increase) on the stock index, based on
    a simulated fundamental growth path.
    """
    
    # --- 1. SET SIMULATION PARAMETERS ---
    
    # Market Parameters
    initial_kospi = 2700      # Starting KOSPI index
    initial_pbr = 0.95        # Current average PBR ("Korea Discount")
    target_pbr = 1.4          # Target PBR (e.g., level of Japan/Taiwan after reforms)
    
    # Time Parameters
    total_years = 10          # Total simulation duration
    policy_years = 5          # Years over which the policy effect phases in
    steps_per_year = 12       # Monthly simulation
    
    # Fundamental Growth Parameters (Simulating the underlying Book Value growth)
    # This represents the "fundamental" earnings/asset growth of the economy
    annual_drift = 0.04       # Assumed annual growth of KOSPI's book value (e.g., 4%)
    annual_volatility = 0.15  # Annual volatility of fundamental growth
    
    
    # --- 2. CALCULATE DERIVED PARAMETERS ---
    
    total_steps = total_years * steps_per_year
    policy_steps = policy_years * steps_per_year
    
    # Convert annual parameters to monthly
    dt = 1 / steps_per_year
    monthly_drift = annual_drift * dt
    monthly_vol = annual_volatility * np.sqrt(dt)
    
    # Calculate the initial Book Value Per Share (BPS) of the index
    initial_bps = initial_kospi / initial_pbr
    
    
    # --- 3. SIMULATE FUNDAMENTAL GROWTH (BOOK VALUE) ---
    
    # We simulate the path of the underlying "Book Value" of the KOSPI.
    # Both scenarios will share this same fundamental path.
    # We use a Geometric Brownian Motion (GBM) for a realistic-looking path.
    
    bps_path = np.zeros(total_steps)
    bps_path[0] = initial_bps
    
    for t in range(1, total_steps):
        random_shock = np.random.normal(0, 1)
        bps_path[t] = bps_path[t-1] * (1 + monthly_drift + random_shock * monthly_vol)
        
        
    # --- 4. CREATE SCENARIOS ---
    
    # Time array for x-axis
    time_axis = np.linspace(0, total_years, total_steps)
    
    # Scenario 1: Baseline (No Policy)
    # KOSPI is just the fundamental book value multiplied by the
    # *constant* low PBR.
    kospi_baseline = bps_path * initial_pbr
    
    # Scenario 2: Policy Scenario (Value-Up)
    # First, create the PBR path as it gradually increases
    pbr_policy_path = np.zeros(total_steps)
    
    # Linearly increase PBR from initial to target over the policy period
    pbr_increase = np.linspace(initial_pbr, target_pbr, policy_steps)
    pbr_policy_path[:policy_steps] = pbr_increase
    
    # After policy period, PBR stays at the new target level
    pbr_policy_path[policy_steps:] = target_pbr
    
    # KOSPI is the fundamental book value multiplied by the
    # *changing* (re-rated) PBR.
    kospi_policy = bps_path * pbr_policy_path
    
    
    # --- 5. VISUALIZE THE RESULTS ---
    
    print("Running simulation...")
    print(f"Initial KOSPI: {initial_kospi:.0f}")
    print(f"Initial PBR: {initial_pbr:.2f}")
    print(f"Target PBR: {target_pbr:.2f} (achieved in {policy_years} years)")
    print(f"---")
    print(f"KOSPI (Baseline) at Year {total_years}: {kospi_baseline[-1]:.0f}")
    print(f"KOSPI (Policy) at Year {total_years}:   {kospi_policy[-1]:.0f}")
    print(f"Difference: {kospi_policy[-1] - kospi_baseline[-1]:.0f} points")

    plt.style.use('seaborn-v0_8-darkgrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, 
                                   gridspec_kw={'height_ratios': [1, 3]})
    
    fig.suptitle('KOSPI "Value-Up" Policy Simulation (Illustrative)', fontsize=18, weight='bold')
    
    # Plot 1: The Policy "Shock" (PBR Change)
    ax1.plot(time_axis, np.full(total_steps, initial_pbr), label='Baseline PBR (Discount)', 
             linestyle='--', color='gray')
    ax1.plot(time_axis, pbr_policy_path, label=f'Policy PBR (Re-rating to {target_pbr})', 
             color='blue', linewidth=2.5)
    ax1.set_title('Policy Assumption: PBR Re-rating')
    ax1.set_ylabel('Market PBR')
    ax1.legend(loc='lower right')
    ax1.axvline(x=policy_years, color='red', linestyle=':', label=f'Policy Target ({policy_years} yrs)')
    
    # Plot 2: The Impact on KOSPI
    ax2.plot(time_axis, kospi_baseline, label='Baseline Forecast (No Policy)', 
             linestyle='--', color='gray', linewidth=2)
    ax2.plot(time_axis, kospi_policy, label='Policy Scenario (Value-Up)', 
             color='blue', linewidth=3)
    
    # Fill the gap between the two scenarios
    ax2.fill_between(time_axis, kospi_baseline, kospi_policy, 
                     where=(kospi_policy > kospi_baseline), 
                     color='blue', alpha=0.1, label='Impact of Re-rating')
    
    ax2.set_title('Simulated Impact on KOSPI Index')
    ax2.set_xlabel('Years')
    ax2.set_ylabel('KOSPI Index Level')
    ax2.legend(loc='upper left')
    ax2.axvline(x=policy_years, color='red', linestyle=':', label=f'Policy Target ({policy_years} yrs)')
    
    # Format y-axis to have commas
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save the figure
    plt.savefig("kospi_value_up_simulation.png", dpi=150)
    print("\nGraph saved as 'kospi_value_up_simulation.png'")
    
    # Show the plot
    plt.show()

if __name__ == "__main__":
    run_policy_simulation()
