import math


def _isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


class Point2(object):
    '''Represents a 2D point.
    '''
    def __init__(self, x=0.0, y=0.0):
        self.__x = float(x)
        self.__y = float(y)

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    def __eq__(self, other):
        return _isclose(self.x, other.x) and _isclose(self.y, other.y)

    def __ne__(self, other):
        return not self == other

    @classmethod
    def from_list(cls, lst):
        x, y = map(float, lst)
        return cls(x, y)


class Point3(object):
    '''Represents a 3D point.
    '''
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.__x = float(x)
        self.__y = float(y)
        self.__z = float(z)

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    @property
    def z(self):
        return self.__z

    def __add__(self, rhs):
        return Point3(self.x + rhs.x, self.y + rhs.y, self.z + rhs.z)

    def __sub__(self, rhs):
        return Point3(self.x - rhs.x, self.y - rhs.y, self.z - rhs.z)

    def __mul__(self, rhs):
        return Point3(self.x * float(rhs), self.y * float(rhs), self.z * float(rhs))

    def __repr__(self):
        return '{0}({1}, {2}, {3})'.format(self.__class__.__name__, self.x, self.y, self.z)

    def distance(self, other_point):
        return math.sqrt((other_point.x - self.x) ** 2 + (other_point.y - self.y) ** 2 + (other_point.z - self.z) ** 2)

    @classmethod
    def from_list(cls, lst):
        x, y, z = map(float, lst)
        return cls(x, y, z)


class Vector3(Point3):
    '''Represents a 3D vector.
    '''
    def __init__(self, x=0.0, y=0.0, z=0.0):
        super(Vector3, self).__init__(x, y, z)

    def __add__(self, rhs):
        if isinstance(rhs, Point3):
            return Vector3(self.x + rhs.x, self.y + rhs.y, self.z + rhs.z)
        elif type(rhs) in [float, int]:
            return Vector3(self.x + float(rhs), self.y + float(rhs), self.z + float(rhs))
        else:
            raise TypeError

    def __sub__(self, rhs):
        if isinstance(rhs, Point3):
            return Vector3(self.x - rhs.x, self.y - rhs.y, self.z - rhs.z)
        elif type(rhs) in [float, int]:
            return Vector3(self.x - float(rhs), self.y - float(rhs), self.z - float(rhs))
        else:
            raise TypeError

    def __mul__(self, rhs):
        if type(rhs) in [float, int]:
            return Vector3(self.x * float(rhs), self.y * float(rhs), self.z * float(rhs))
        else:
            # Do not allow dot or cross products with multiplication operator due to ambiguity issues
            raise TypeError

    def dot(self, vector3):
        '''Dot product.'''
        return self.x * vector3.x + self.y * vector3.y + self.z * vector3.z

    def magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalize(self):
        return self * (1.0 / self.magnitude())

    def angle(self, vector3):
        '''Return the angle between two vectors in degrees.'''
        return math.degrees(math.acos((self.dot(vector3) / (self.magnitude() * vector3.magnitude()))))

    @classmethod
    def from_points(cls, from_point, to_point):
        if isinstance(from_point, Point3) and isinstance(to_point, Point3):
            displacement = to_point - from_point
            return cls(displacement.x, displacement.y, displacement.z)
        raise TypeError
