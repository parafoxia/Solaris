# Solaris - A Discord bot designed to make your server a safer and better place.
# Copyright (C) 2020  Ethan Henderson

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Ethan Henderson
# parafoxia@carberra.xyz


class Match:
    def __init__(self, term, comparison, case_sensitive=False):
        self.term = term
        self.comparison = comparison
        self.case_sensitive = case_sensitive
        self._strength = self._calculate_strength()

    @property
    def strength(self):
        return self._strength

    def _calculate_strength(self):
        most_matches = 0

        for idx in range(len(self.comparison)):
            matches = 0
            term = self.term if self.case_sensitive else self.term.lower()
            comparison = (self.comparison if self.case_sensitive else self.comparison.lower())[idx:]

            for idx2 in range(min(len(term), len(comparison))):
                if term[idx2] == comparison[idx2]:
                    matches += 1

            if matches > most_matches:
                most_matches = matches

        return most_matches / len(self.term)

    def __str__(self, /):
        return self.comparison

    def __repr__(self, /):
        return f"<Match comparison={repr(self.comparison)} strength={repr(self.strength)}>"

    def __int__(self, /):
        return int(self.strength)

    def __round__(self, /):
        return round(self.strength)

    def __float__(self, /):
        return self.strength

    def __eq__(self, value, /):
        return self.comparison == value.comparison

    def __ne__(self, value, /):
        return self.comparison != value.comparison


class Search:
    def __init__(self, term, comparisons, case_sensitive=False):
        self.term = term
        self.comparisons = comparisons
        self._matches = [Match(term, c, case_sensitive) for c in comparisons]

    @property
    def matches(self):
        return self._matches

    def best(self, min_accuracy=0):
        if (match := max(self.matches, key=lambda x: x.strength)).strength >= min_accuracy:
            return match

    def worst(self):
        return min(self.matches, key=lambda x: x.strength)

    def top(self, limit=1):
        return sorted(self.matches, key=lambda x: x.strength, reverse=True)[:limit]

    def bottom(self, limit=1):
        return sorted(self.matches, key=lambda x: x.strength, reverse=True)[-limit:]

    def range(self, min, max):
        return sorted(self.matches, key=lambda x: x.strength, reverse=True)[min:max]

    def accurate_to(self, accuracy):
        return sorted([m for m in self.matches if m.strength >= accuracy], key=lambda x: x.strength, reverse=True)

    def __str__(self, /):
        return self.term

    def __repr__(self, /):
        return f"<Search term={repr(self.term)} comparisons={repr(len(self.comparisons))}>"

    def __int__(self, /):
        return int(self.matches)

    def __round__(self, /):
        return round(self.matches)

    def __float__(self, /):
        return self.matches
