import biosteam as bst, qsdsan as qs


class Pump(bst.units.Pump): 

    @property
    def add_OPEX(self):
        if not hasattr(self, "_add_OPEX"):
            self._add_OPEX = 0.0  # Default OPEX if missing

        return {'Additional OPEX': self._add_OPEX} if isinstance(self._add_OPEX, (float, int)) \
            else self._add_OPEX


    @property
    def uptime_ratio(self):
        if not hasattr(self, "_uptime_ratio"):
            self._uptime_ratio = 0.9  # Default OPEX if missing
        return self._uptime_ratio