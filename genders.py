"""Gender objects."""

genders = []

class Gender(object):
 def __init__(self,
  sex,
  he,
  she,
  him,
  her,
  his,
  hers
 ):
  self.sex = sex
  self.he = he
  self.she = she
  self.him = him
  self.her = her
  self.his = his
  self.hers = hers

MALE = Gender('male', 'he', 'he', 'him', 'him', 'his', 'his')
FEMALE = Gender('female', 'she', 'she', 'her', 'her', 'her', 'hers')

genders.append(MALE)
genders.append(FEMALE)
NEUTRAL = Gender('neutral', 'it', 'it', 'it', 'it', "it's", "it's")

genders.append(NEUTRAL)
