from dataclasses import dataclass, field, asdict
from typing import Dict

@dataclass
class EVModel:
    name: str = 'Hyderabad Retrofit EV'
    battery_capacity_kwh: float = 7.0
    usable_battery_fraction: float = 0.95
    efficiency_km_per_kwh: float = 7.5
    charger_power_kw: float = 6.0
    charging_efficiency: float = 0.92
    dc_fast_charge_power_kw: float = 15.0
    dc_fast_charge_efficiency: float = 0.94
    reserve_soc_fraction: float = 0.20
    aux_load_kw: float = 0.15
    fuel_fill_minutes_reference: float = 5.0
    assumptions: Dict[str, float] = field(default_factory=lambda: {
        'city': 'Hyderabad, Telangana',
        'base_use_case': 'Retrofitted electric autorickshaw',
        'default_daily_km': 160.0,
        'notes': 'Use efficiency based on similar market models and adjust after road trials.'
    })

    @property
    def usable_battery_kwh(self) -> float:
        return self.battery_capacity_kwh * self.usable_battery_fraction

    @property
    def effective_driveable_battery_kwh(self) -> float:
        return self.usable_battery_kwh * (1 - self.reserve_soc_fraction)

    @property
    def consumption_kwh_per_km(self) -> float:
        return 1 / self.efficiency_km_per_kwh

    def range_full(self) -> float:
        return self.usable_battery_kwh * self.efficiency_km_per_kwh

    def range_practical(self) -> float:
        return self.effective_driveable_battery_kwh * self.efficiency_km_per_kwh

    def distance_for_soc_window(self, start_soc_pct: float, end_soc_pct: float, include_reserve: bool = True) -> float:
        soc_delta = max(0.0, (start_soc_pct - end_soc_pct) / 100.0)
        available_kwh = self.usable_battery_kwh * soc_delta
        if include_reserve:
            minimum_kwh = self.usable_battery_kwh * self.reserve_soc_fraction
            available_kwh = max(0.0, available_kwh - minimum_kwh)
        return available_kwh * self.efficiency_km_per_kwh

    def energy_needed_for_distance(self, distance_km: float) -> float:
        return distance_km * self.consumption_kwh_per_km

    def soc_drop_for_distance(self, distance_km: float) -> float:
        return (self.energy_needed_for_distance(distance_km) / self.usable_battery_kwh) * 100

    def distance_remaining_from_soc(self, soc_pct: float) -> float:
        usable_soc = max(0.0, (soc_pct / 100.0) - self.reserve_soc_fraction)
        return usable_soc * self.usable_battery_kwh * self.efficiency_km_per_kwh

    def charging_time_hours(self, start_soc_pct: float, target_soc_pct: float, mode: str = 'ac') -> float:
        soc_delta = max(0.0, (target_soc_pct - start_soc_pct) / 100.0)
        energy_needed_kwh = self.usable_battery_kwh * soc_delta
        if mode.lower() == 'dc':
            effective_power = self.dc_fast_charge_power_kw * self.dc_fast_charge_efficiency
        else:
            effective_power = self.charger_power_kw * self.charging_efficiency
        return energy_needed_kwh / effective_power if effective_power > 0 else 0.0

    def charging_time_minutes(self, start_soc_pct: float, target_soc_pct: float, mode: str = 'ac') -> float:
        return self.charging_time_hours(start_soc_pct, target_soc_pct, mode) * 60

    def power_needed_for_target_charge_time(self, start_soc_pct: float, target_soc_pct: float, target_hours: float, mode: str = 'ac') -> float:
        soc_delta = max(0.0, (target_soc_pct - start_soc_pct) / 100.0)
        energy_needed_kwh = self.usable_battery_kwh * soc_delta
        eff = self.dc_fast_charge_efficiency if mode.lower() == 'dc' else self.charging_efficiency
        return energy_needed_kwh / (target_hours * eff) if target_hours > 0 and eff > 0 else 0.0

    def charging_energy_from_grid(self, start_soc_pct: float, target_soc_pct: float, mode: str = 'ac') -> float:
        soc_delta = max(0.0, (target_soc_pct - start_soc_pct) / 100.0)
        battery_energy_kwh = self.usable_battery_kwh * soc_delta
        eff = self.dc_fast_charge_efficiency if mode.lower() == 'dc' else self.charging_efficiency
        return battery_energy_kwh / eff if eff > 0 else 0.0

    def charging_cost(self, start_soc_pct: float, target_soc_pct: float, tariff_per_kwh: float, mode: str = 'ac') -> float:
        return self.charging_energy_from_grid(start_soc_pct, target_soc_pct, mode) * tariff_per_kwh

    def average_power_with_aux_load(self, traction_power_kw: float) -> float:
        return traction_power_kw + self.aux_load_kw

    def runtime_hours_for_power_draw(self, average_total_power_kw: float, soc_pct: float = 100.0) -> float:
        available_kwh = (soc_pct / 100.0) * self.usable_battery_kwh
        return available_kwh / average_total_power_kw if average_total_power_kw > 0 else 0.0

    def summary(self) -> Dict[str, float]:
        return {
            'name': self.name,
            'battery_capacity_kwh': self.battery_capacity_kwh,
            'usable_battery_kwh': round(self.usable_battery_kwh, 2),
            'effective_driveable_battery_kwh': round(self.effective_driveable_battery_kwh, 2),
            'efficiency_km_per_kwh': self.efficiency_km_per_kwh,
            'consumption_kwh_per_km': round(self.consumption_kwh_per_km, 4),
            'full_range_km': round(self.range_full(), 2),
            'practical_range_km': round(self.range_practical(), 2),
            'ac_charger_power_kw': self.charger_power_kw,
            'dc_fast_charge_power_kw': self.dc_fast_charge_power_kw,
            'fuel_fill_minutes_reference': self.fuel_fill_minutes_reference,
        }


if __name__ == '__main__':
    ev = EVModel(
        battery_capacity_kwh=4.0,
        efficiency_km_per_kwh=7.5,
        charger_power_kw=4.0,
        dc_fast_charge_power_kw=8.0,
    )

    print('MODEL SUMMARY')
    print(ev.summary())
    print('\nDISTANCE FROM 90% TO 20% SOC')
    print(round(ev.distance_for_soc_window(90, 20), 2), 'km')
    print('\nCHARGING TIME 20% TO 80% AC')
    print(round(ev.charging_time_minutes(20, 80, mode='ac'), 2), 'minutes')
    print('\nCHARGING TIME 20% TO 80% DC')
    print(round(ev.charging_time_minutes(20, 80, mode='dc'), 2), 'minutes')
    print('\nPOWER NEEDED TO CHARGE 20% TO 80% IN 30 MIN')
    print(round(ev.power_needed_for_target_charge_time(20, 80, 0.5, mode='dc'), 2), 'kW')
