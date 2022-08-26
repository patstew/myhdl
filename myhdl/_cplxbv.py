#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2015 Jan Decaluwe
#
#  The myhdl library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public License as
#  published by the Free Software Foundation; either version 2.1 of the
#  License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.

#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" Module with the intbv class """
from __future__ import absolute_import, division


from myhdl._compat import long, integer_types, string_types, builtins
from myhdl._bin import bin
from myhdl._fixbv import fixbv


class cplxbv(object):
    #__slots__ = ('_val', '_min', '_max', '_nrbits', '_handleBounds')

    def __init__(self, re=0, im = 0, msb=1, lsb=0, mult_mode = 'simple'):
        if isinstance(re, fixbv) and isinstance(im, fixbv):
            self.re = re
            self.im = im
        else:
            self.re = fixbv(re, msb, lsb)
            self.im = fixbv(im, msb, lsb)

    def __iadd__(self, other):
        if isinstance(other, cplxbv):
            self.re += other.re
            self.im += other.im
        else:
            self.re += other
        return self
            
    def __add__(self, other):
        if isinstance(other, cplxbv):
            return cplxbv(self.re + other.re, self.im + other.im)
        else:
            return cplxbv(self.re + other, self.im)

    def __radd__(self, other):
        return other + self._val

"""
    def __sub__(self, other):
        if not isinstance(other, fixbv):
            res = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max)
        else:
            res = other.__copy__()
        res -= self
        return res

    def __rsub__(self, other):
        return other - self._val

    def __mul__(self, other):
        if not isinstance(other, fixbv):
            res = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max)
        else:
            res = other.__copy__()
        res *= self
        return res

    def __rmul__(self, other):
        return other * self._val

    def __truediv__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max)
        res = self.__copy__()
        res /= other
        return res

    def __rtruediv__(self, other):
        return other / self._val

    def __floordiv__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max)
        res = self.__copy__()
        res //= other
        return res

    def __rfloordiv__(self, other):
        return other // self._val

    def __mod__(self, other):
        return self._val % int(other * 2**self._frac)

    def __rmod__(self, other):
        return other % self._val

    def __pow__(self, other):
        res = self.__copy__()
        res **= other
        return res

    def __rpow__(self, other):
        raise NotImplementedError()

    def __lshift__(self, other):
        res = self.__copy__()
        res <<= other
        return res

    def __rlshift__(self, other):
        return other << self._val

    def __rshift__(self, other):
        res = self.__copy__()
        res >>= other
        return res

    def __rrshift__(self, other):
        return other >> self._val

    def __and__(self, other):
        raise NotImplementedError()

    def __rand__(self, other):
        raise NotImplementedError()

    def __or__(self, other):
        raise NotImplementedError()

    def __ror__(self, other):
        raise NotImplementedError()

    def __xor__(self, other):
        raise NotImplementedError()

    def __rxor__(self, other):
        raise NotImplementedError()

    def __iadd__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max)
        
        if other._frac > self._frac:
            self._val = (self._val << other._frac - self._frac) + other._val
            self._min <<= other._frac - self._frac
            self._max <<= other._frac - self._frac
        else:
            self._val = self._val + (other._val << self._val - other._frac)
            
        _frac = self._frac
        self._frac = max(self._frac, other._frac)
        self._nrbits = max(self._nrbits - _frac, other._nrbits - other._frac) + self._frac

        self._handleBounds()
        return self

    def __isub__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max)
        
        if other._frac > self._frac:
            self._val = (self._val << other._frac - self._frac) - other._val
            self._min <<= other._frac - self._frac
            self._max <<= other._frac - self._frac
        else:
            self._val = self._val - (other._val << self._val - other._frac)
            
        _frac = self._frac
        self._frac = max(self._frac, other._frac)
        self._nrbits = max(self._nrbits - _frac, other._nrbits - other._frac) + self._frac

        self._handleBounds()
        return self

    def __imul__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max)
            
        self._val *= other._val
        self._nrbits += other._nrbits
        self._frac += other._frac
        self._min <<= other._frac
        self._max <<= other._frac
        
        self._handleBounds()
        return self

    def __ifloordiv__(self, other):
        if isinstance(other, fixbv):
            self._val <<= other._frac
            self._min <<= other._frac
            self._max <<= other._frac
            self._nrbits += other._frac
            self._val //= other._val
        else:
            self._val //= other
        self._handleBounds()
        return self

    def __idiv__(self, other):
        if isinstance(other, fixbv):
            self._val <<= other._frac
            self._min <<= other._frac
            self._max <<= other._frac
            self._nrbits += other._frac
            self._val /= other._val
        else:
            self._val /= other
        self._handleBounds()
        return self

    def __itruediv__(self, other):
        if isinstance(other, fixbv):
            self._val <<= other._frac
            self._min <<= other._frac
            self._max <<= other._frac
            self._nrbits += other._frac
            self._val /= other._val
        else:
            self._val /= other
        self._handleBounds()
        return self

    def __imod__(self, other):
        if isinstance(other, intbv):
            self._val %= other._val
        else:
            self._val %= other
        self._handleBounds()
        return self

    def __ipow__(self, other, modulo=None):
        # XXX why 3rd param required?
        # unused but needed in 2.2, not in 2.3
        if not isinstance(other, integer_types) or other < 1:
            raise ValueError("fixbv only supports integer powers >= 1")
        self._val **= other
        self._nrbits *= other
        self._min <<= self._frac * (other - 1)
        self._max <<= self._frac * (other - 1)
        self._frac *= other
        self._handleBounds()
        return self

    def __iand__(self, other):
        raise NotImplementedError()

    def __ior__(self, other):
        raise NotImplementedError()

    def __ixor__(self, other):
        raise NotImplementedError()

    def __ilshift__(self, other):
        other = int(other)
        if other > self._frac:
            self._val << other - self._frac
            self._min >>= self._frac
            self._max >>= self._frac
            self._frac = 0
        else:
            self._frac -= other
            self._min >>= other
            self._max >>= other
        self._handleBounds()
        return self

    def __irshift__(self, other):
        other = int(other)
        self._frac += other
        self._min <<= other
        self._max <<= other
        self._handleBounds()
        return self

    def __neg__(self):
        res = self.__copy__()
        res._val = -res._val
        return res

    def __pos__(self):
        return self

    def __abs__(self):
        if self < 0:
            return -self
        else:
            return self

    def __invert__(self):
        if self._nrbits and self._min >= 0:
            return fixbv(~self._val & (long(1) << self._nrbits) - 1, min=self._min, max=self._max, _nrbits=self._nrbits, _frac=self._frac)
        else:
            return fixbv(~self._val, min=self._min, max=self._max, _nrbits=self._nrbits, _frac=self._frac)

    def __int__(self):
        return int(self._val) >> self._frac

    def __long__(self):
        return long(self._val) >> self._frac

    def __float__(self):
        return float(self._val) / 2**self._frac

    # XXX __complex__ seems redundant ??? (complex() works as such?)

    def __oct__(self):
        return oct(self._val)

    def __hex__(self):
        return hex(self._val)

    def __index__(self):
        return int(self._val) >> self._frac

    # comparisons
    def __eq__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max)
            
        if self._frac > other._frac:
            return self._val == other._val << self._frac - other._frac
        else:
            return self._val << other._frac - self._frac == other._val
            
    def __ne__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max)
            
        if self._frac > other._frac:
            return self._val != other._val << self._frac - other._frac
        else:
            return self._val << other._frac - self._frac != other._val

    def __lt__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max)
            
        if self._frac > other._frac:
            return self._val < other._val << self._frac - other._frac
        else:
            return self._val << other._frac - self._frac < other._val

    def __le__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max)
            
        if self._frac > other._frac:
            return self._val <= other._val << self._frac - other._frac
        else:
            return self._val << other._frac - self._frac <= other._val

    def __gt__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max)
            
        if self._frac > other._frac:
            return self._val > other._val << self._frac - other._frac
        else:
            return self._val << other._frac - self._frac > other._val

    def __ge__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max)
            
        if self._frac > other._frac:
            return self._val >= other._val << self._frac - other._frac
        else:
            return self._val << other._frac - self._frac >= other._val

    # representation
    def __str__(self):
        return str(float(self))

    def __repr__(self):
        return "fixbv(" + float(self) + ")"
"""
