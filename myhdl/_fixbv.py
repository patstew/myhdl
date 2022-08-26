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

from math import ceil
from myhdl._compat import long, integer_types, string_types, builtins
from myhdl._bin import bin
from myhdl._intbv import intbv


class fixbv(intbv):
    #__slots__ = ('_val', '_min', '_max', '_nrbits', '_handleBounds')

    #rounding = 'floor', 'ceil', 'nearest'
    def __init__(self, val=0, msb=1, lsb=0, min=None, max=None, saturate=False, rounding='floor', _nrbits=0, _frac=0):
        if msb <= lsb:
            raise ValueError("MSB <= LSB")
            
        if _nrbits and _frac: #Construct from exact values for internal purposes
            self._nrbits = _nrbits
            self._frac = _frac
            self._val = val
            self._min = min
            self._max = max
        else: #Normal constructor
            self._nrbits = msb - lsb
            self._frac = -lsb
            if min or max:
                self._min = int(min * 2**self._frac)
                self._max = int(max * 2**self._frac)
            else:
                self._max = 1 << self._nrbits-1
                self._min = -self._max
            if isinstance(val, fixbv):
                self._val = val._val
                self._min = val._min
                self._max = val._max
                self._nrbits = val._nrbits
                self._frac = val._frac
            else:
                self._val = int(val * 2**self._frac)
        
        self._handleBounds()
        self.rounding = rounding
        self.saturate = saturate

    # support for the 'min' and 'max' attribute
    @property
    def max(self):
        return self._max / 2**self._frac

    @property
    def min(self):
        return self._min / 2**self._frac

    # copy methods
    def __copy__(self):
        return type(self)(self._val, min=self._min, max=self._max, _nrbits=self._nrbits, _frac=self._frac, rounding = self.rounding, saturate = self.saturate)

    def __deepcopy__(self, visit):
        return type(self)(self._val, min=self._min, max=self._max, _nrbits=self._nrbits, _frac=self._frac, rounding = self.rounding, saturate = self.saturate)

    def __getitem__(self, key):
        if isinstance(key, slice):
            i, j = key.start, key.stop
            if j is None:  # default
                j = 0
            j = int(j)
            if j < -self._frac:
                raise ValueError("intbv[i:j] requires j >= LSB\n"
                                 "            j == %s" % j)
            
            if i is None:  # default
                i = self._nrbits - self._frac
            i = int(i)
            if i <= j or i > self._nrbits - self._frac:
                raise ValueError("intbv[i:j] requires msb+1 >= i > j\n"
                                 "            i, j == %s, %s" % (i, j))
            
            res = self.__copy__()
            res._frac = -j
            res._nrbits = i - j
            j += self._frac
            res._max >>= j
            res._min >>= j
            res._val >>= j
            res._val &= (1 << res._nrbits) - 1
            return res
        else:
            i = int(key)
            res = bool((self._val >> i) & 0x1)
            return res

    def __setitem__(self, key, val):
        if isinstance(key, slice):
            i, j = key.start, key.stop
            if j is None:  # default
                j = 0
            else:
                if j < self._frac:
                    raise ValueError("fixbv[i:j] = v requires j >= lsb\n"
                                     "            j == %s" % j)
                j = int(j) + self._frac
            if i is None:
                i = self._nrbits
            else:
                i = int(i) + self._frac
                if i <= j or i > self._nrbits:
                    raise ValueError("intbv[i:j] requires msb+1 >= i > j\n"
                                     "            i, j == %s, %s" % (i - self._frac, j - self._frac))
            
            if isinstance(val, intbv) and val._nrbits == i - j:
                val = val._val
            elif not isinstance(val, integer_types):
                raise ValueError("fixbv[i:j] = v requires v to be an integer or a correctly sized intbv or fixbv slice")
            mask = ((long(1) << i-j) - 1) << j
            self._val = ((val << j) & mask) | (self._val & ~mask)

            self._handleBounds()
        else:
            i = int(key) + self._frac
            if val == 1:
                self._val |= (long(1) << i)
            elif val == 0:
                self._val &= ~(long(1) << i)
            else:
                raise ValueError("fixbv[i] = v requires v in (0, 1)\n"
                                 "            i == %s " % i)

            self._handleBounds()

    @property
    def val(self):
        return self._val
        
    @val.setter
    def val(self, other):
        if isinstance(other, fixbv):
            if other._frac == self._frac:
                self._val = other._val
            elif other._frac < self._frac:
                self._val = other._val << self._frac - other._frac
            else:
                if self.rounding == 'floor':
                    self._val = other._val >> other._frac - self._frac
                elif self.rounding == 'ceil':
                    self._val = other._val + (1 << other._frac - self._frac) - 1 >> other._frac - self._frac
                elif self.rounding == 'nearest':
                    self._val = other._val + (1 << other._frac - self._frac - 1) >> other._frac - self._frac
                else:
                    raise AttributeError('Invalid rounding mode "%s"' % self.rounding)
        elif isinstance(other, intbv):
            self._val = other._val << self._frac
        elif isinstance(other, integer_types):
            self._val = other << self._frac
        elif isinstance(other, float):
            if self.rounding == 'floor':
                self._val = int(other * 2**self._frac)
            elif self.rounding == 'ceil':
                self._val = int(ceil(other * 2**self._frac))
            elif self.rounding == 'nearest':
                self._val = int(other * 2**self._frac + 0.5)
            else:
                raise AttributeError('Invalid rounding mode "%s"' % self.rounding)
        else:
            raise ValueError("Unsupported type to assign to fixbv.val")
        
        if self.saturate:
            if self._val > self._max:
                self._val = self._max
            if self._val < self._min:
                self._val = self._min
            
        self._handleBounds()
                    
    # integer-like methods

    def __add__(self, other):
        if not isinstance(other, fixbv):
            res = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max, rounding = self.rounding, saturate = self.saturate)
        else:
            res = other.__copy__()
        res += self
        return res

    def __radd__(self, other):
        return other + self._val

    def __sub__(self, other):
        if not isinstance(other, fixbv):
            res = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max, rounding = self.rounding, saturate = self.saturate)
        else:
            res = other.__copy__()
        res -= self
        return res

    def __rsub__(self, other):
        return other - self._val

    def __mul__(self, other):
        if not isinstance(other, fixbv):
            res = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max, rounding = self.rounding, saturate = self.saturate)
        else:
            res = other.__copy__()
        res *= self
        return res

    def __rmul__(self, other):
        return other * self._val

    def __truediv__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max, rounding = self.rounding, saturate = self.saturate)
        res = self.__copy__()
        res /= other
        return res

    def __rtruediv__(self, other):
        return other / self._val

    def __floordiv__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max, rounding = self.rounding, saturate = self.saturate)
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
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max, rounding = self.rounding, saturate = self.saturate)
        
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
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max, rounding = self.rounding, saturate = self.saturate)
        
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
            other = fixbv(other, self._nrbits - self._frac, -self._frac, self._min, self._max, rounding = self.rounding, saturate = self.saturate)
            
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
            return fixbv(~self._val & (long(1) << self._nrbits) - 1, min=self._min, max=self._max, _nrbits=self._nrbits, _frac=self._frac, rounding = self.rounding, saturate = self.saturate)
        else:
            return fixbv(~self._val, min=self._min, max=self._max, _nrbits=self._nrbits, _frac=self._frac, rounding = self.rounding, saturate = self.saturate)

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
            other = fixbv(other, self._nrbits - self._frac, -self._frac)
            
        if self._frac > other._frac:
            return self._val == other._val << self._frac - other._frac
        else:
            return self._val << other._frac - self._frac == other._val
            
    def __ne__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac)
            
        if self._frac > other._frac:
            return self._val != other._val << self._frac - other._frac
        else:
            return self._val << other._frac - self._frac != other._val

    def __lt__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac)
            
        if self._frac > other._frac:
            return self._val < other._val << self._frac - other._frac
        else:
            return self._val << other._frac - self._frac < other._val

    def __le__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac)
            
        if self._frac > other._frac:
            return self._val <= other._val << self._frac - other._frac
        else:
            return self._val << other._frac - self._frac <= other._val

    def __gt__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac)
            
        if self._frac > other._frac:
            return self._val > other._val << self._frac - other._frac
        else:
            return self._val << other._frac - self._frac > other._val

    def __ge__(self, other):
        if not isinstance(other, fixbv):
            other = fixbv(other, self._nrbits - self._frac, -self._frac)
            
        if self._frac > other._frac:
            return self._val >= other._val << self._frac - other._frac
        else:
            return self._val << other._frac - self._frac >= other._val

    # representation
    def __str__(self):
        return str(float(self))

    def __repr__(self):
        return "fixbv(" + float(self) + ")"

