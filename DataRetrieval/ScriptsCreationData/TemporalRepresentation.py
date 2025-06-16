import numpy as np
import copy

class Timerepresentation:
	
	type_of_temporal_representation = str
	
	def __init__(self, type_of_temporal_representation):
		self.type_of_temporal_representation = type_of_temporal_representation

	def __str__(self):
		self.__str__()


class Interval(Timerepresentation):

	start = np.datetime64 
	end = np.datetime64

	def __init__(self, start:np.datetime64, end:np.datetime64) -> None:
		super().__init__("Interval")
		if  start == None or end == None or start <= end:
			self.start = start
			self.end = end
		else:
			#print("Interval inversed !")
			self.start = end
			self.end = start

	def __str__(self) -> str:
		return str((self.start, self.end))
	
	def __repr__(self) -> str:
		return str(self)

	def __hash__(self) -> int:
		return hash((self.start, self.end))

	def _is_valid_operand(self, other):
		return (hasattr(other, "start") * hasattr(other, "end"))

	def __eq__(self, other):
		if not self._is_valid_operand(other):
			return NotImplemented
		return (self.start==other.start) * (self.end==other.end)
	
	def output_to_file(self):
		return f"{self.start}\t{self.end}"

	def get_start(self) -> np.datetime64:
		return self.start

	def get_end(self) -> np.datetime64:
		return self.end
	
	def update_start(self, new_start:np.datetime64) -> np.datetime64:
		self.start = new_start
	
	def update_end(self, new_end:np.datetime64) -> np.datetime64:
		self.end = new_end

	def day_in_the_interval(self, temporal_granularity:str="D", default_start:np.datetime64=None, default_end:np.datetime64=None) -> int:
		if self.start and self.end:
			return (self.end - self.start).astype(int)#(self.end - self.start).astype(temporal_granularity).astype(int)
		else:
			start = self.start 
			end = self.end 
			if (not self.start and not default_start) or (not self.end and not default_end):
				print("A default setting must be set")
				return None
			if (not self.start):
				start = default_start
			if (not self.end):
				end = default_end
			return  (end - start).astype(int)

	#### ALLEN'S AXIOMS

	# The end of A is before the start of B
	def is_A_before(self, other) -> bool:
		return self.get_end() < other.get_start()
	
	# Both intervals are equal
	def is_A_equal(self, other) -> bool:
		return (self.get_start() == other.get_start()) \
			& (self.get_end() == other.get_end())
	
	# The end of A is the start of B 
	def is_A_meets(self, other) -> bool:
		return self.get_end() == other.get_start()
	
	# The end of A is after the start of B & before the end of B
	def is_A_overlaps(self, other) -> bool:
		return (self.get_start() < other.get_start())\
			& (self.get_end() > other.get_start()) \
			& (self.get_end() < other.get_end())
	
	# The start of A is after the start of B and the end of A is before the end of B
	def is_A_during(self, other) -> bool:
		return ((self.get_start() > other.get_start()) & (self.get_end() < other.get_end()))
		# return ((self.get_start() > other.get_start()) & (self.get_end() <= other.get_end())) \
		#     or ((self.get_start() >= other.get_start()) & (self.get_end() < other.get_end()))
	
	# A and B start together but A finishes first
	def is_A_starts(self, other) -> bool:
		return (self.get_start() == other.get_start()) \
			& (self.get_end() < other.get_end())
	
	# B starts before A but finishes with A
	def is_A_finishes(self, other) -> bool:
		return (self.get_start() > other.get_start()) \
			& (self.get_end() == other.get_end())
	
	# Launch every verification of the axioms 
	def is_A_verification(self, other) -> dict():
		return {"before":self.is_A_before(other),
				"equal":self.is_A_equal(other),
				"meets":self.is_A_meets(other),
				"overlaps":self.is_A_overlaps(other),
				"during":self.is_A_during(other),
				"starts":self.is_A_starts(other),
				"finishes":self.is_A_finishes(other)}

class Timestamp(Timerepresentation):
	date = np.datetime64

	def __init__(self, date:np.datetime64) -> None:
		super().__init__("Timestamp")
		self.date = date

	def get_date(self):
		return self.date
	
	def __str__(self):
		return str(self.date)
	
	def __repr__(self) -> str:
		return str(self)

	def __hash__(self):
		return hash(self.date)
	
	def output_to_file(self):
		return f"{self.date}"

class Triple:

	head = int
	relation = int
	value = int
	date = Timerepresentation
	is_object = bool

	def __init__(self, head:int, relation:int, value, date:Timerepresentation, is_object:bool=True) -> None:
		self.head = head
		self.relation = relation
		self.value = value
		self.date = date
		self.is_object = is_object

	def __str__(self) -> str:
		return str((self.head, self.relation, self.value, self.date, self.is_object))
	
	def __repr__(self) -> str:
		return str(self)

	def __hash__(self) -> int:
		return hash((self.head, self.relation, self.value, str(self.date)))
	
	def __eq__(self, other) -> bool:
		return (self.head == other.head) \
			& (self.relation == other.relation) \
			& (self.value == other.value) \
			& (self.date == other.date) 
	
	def output_to_file(self, res_is_object=False):
		res= f"{self.head}\t{self.relation}\t{self.value}\t{self.date.output_to_file()}"
		if res_is_object:
			res += f"\t{self.is_object}"
		return res

class Entity:

	name = str
	life_span = Interval
	triples_per_r_as_head = dict
	triples_per_r_as_tale = dict
	today = np.datetime64
	temporal_precision = str


	def __init__(self, name:str, today:np.datetime64, temporal_precision:str) -> None:
		self.name = name
		self.life_span = Interval(None, None)
		self.triples_per_r_as_head = {}
		self.triples_per_r_as_tale = {}
		self.today = today
		self.temporal_precision = temporal_precision 

	def __str__(self) -> str:
		return str((self.name, str(self.life_span)))

	def __repr__(self) -> str:
		return str(self)

	def __hash__(self):
		return hash(self.name)
	
	def add_triple(self, triple:Triple, is_head:bool=True) -> None:

		if is_head:
			if not triple.relation in self.triples_per_r_as_head:
				self.triples_per_r_as_head[triple.relation] = set()

			self.triples_per_r_as_head[triple.relation].add(triple)
		else:
			if not triple.relation in self.triples_per_r_as_tale:
				self.triples_per_r_as_tale[triple.relation] = set()

			self.triples_per_r_as_tale[triple.relation].add(triple)
		
		if triple.date.type_of_temporal_representation == "Interval":
			if (triple.date.get_start() != None):
				if (self.life_span.get_start() != None) and\
						(self.life_span.get_start() > triple.date.get_start()):
					self.life_span.update_start(new_start=triple.date.get_start())
				elif (self.life_span.get_start() == None):
					self.life_span.update_start(new_start=triple.date.get_start())

				if (self.life_span.get_end() != None) and\
						(self.life_span.get_end() < triple.date.get_start()):
					self.life_span.update_end(new_end=triple.date.get_start()+np.timedelta64(1,self.temporal_precision))
				elif (self.life_span.get_end() == None):
					self.life_span.update_end(new_end=triple.date.get_start()+np.timedelta64(1,self.temporal_precision))

			if (triple.date.get_end() != None):
				if (self.life_span.get_end() != None) and\
						(self.life_span.get_end() < triple.date.get_end()):
					self.life_span.update_end(new_end=triple.date.get_end())
				elif (self.life_span.get_end() == None):
					self.life_span.update_end(new_end=triple.date.get_end())

				if (self.life_span.get_start() != None) and\
						(self.life_span.get_start() > triple.date.get_end()):
					self.life_span.update_start(new_start=triple.date.get_end()-np.timedelta64(1,self.temporal_precision))
				elif (self.life_span.get_start() == None):
					self.life_span.update_start(new_start=triple.date.get_end()-np.timedelta64(1,self.temporal_precision))
			else:
				self.life_span.update_end(self.today)
		else:
			if (self.life_span.get_start() == None):
				self.life_span.start = triple.date.get_date()
			elif self.life_span.start > triple.date.get_date():
				self.life_span.start = triple.date.get_date()
			
			if (self.life_span.get_end() == None):
				self.life_span.end = triple.date.get_date()
			elif self.life_span.end < triple.date.get_date():
				self.life_span.end = triple.date.get_date()

	def update_lifespan(self) -> None:

		new_early = None
		new_latest = None

		for stored_triples in [self.triples_per_r_as_head, self.triples_per_r_as_tale]:
			for r in stored_triples:
				for t in stored_triples[r]:
					if t.date.type_of_temporal_representation == "Interval":
						if new_early == None and t.date.get_start() != None:
							new_early = t.date.get_start()
						elif t.date.get_start() != None and new_early>t.date.get_start():
							new_early = t.date.get_start()
						elif t.date.get_end() != None and (new_early == None or new_early>t.date.get_end()-np.timedelta64(1,self.temporal_precision)):
							new_early = t.date.get_end()-np.timedelta64(1,self.temporal_precision)
						
						if t.date.get_end() == None:
							new_latest = self.today
						elif new_latest == None:
							new_latest = t.date.get_end()
						elif new_latest < t.date.get_end():
							new_latest = t.date.get_end()
					
					else:
						if (new_early == None):
							new_early = t.date.get_date()
						elif new_early > t.date.get_date():
							new_early = t.date.get_date()
						
						if (new_latest == None):
							new_latest = t.date.get_date()
						elif new_latest < t.date.get_date():
							new_latest = t.date.get_date()
		
		self.life_span = Interval(new_early, new_latest)


	def get_lifespan(self):
		return self.life_span
	
	def get_number_of_days(self):
		return self.life_span.day_in_the_interval()
	
	def get_triples_with_r(self, r, as_head:bool=True):
		if as_head:
			if r in self.triples_per_r_as_head:
				return self.triples_per_r_as_head[r]
			return None
		else:
			if r in self.triples_per_r_as_tale:
				return self.triples_per_r_as_tale[r]
			return None

def ordered_time_sequence_first_start(entity:Entity, r:str, as_head:bool=True, temporal_granularity:str="D"):
	triples_of_r = entity.get_triples_with_r(r, as_head)
	if triples_of_r != None:
		r_per_start = {}
		for t in triples_of_r:

			if t.date.type_of_temporal_representation == "Interval":

				start_triple, end_triple = t.date.get_start(), t.date.get_end()
				
				if start_triple == None:
					start_triple = entity.get_lifespan().get_start()
					if start_triple == end_triple:
						start_triple -= np.timedelta64(1, temporal_granularity)


				if end_triple == None:
					end_triple = entity.get_lifespan().get_end()
					if start_triple == end_triple:
						end_triple += np.timedelta64(1, temporal_granularity)

				if not start_triple in r_per_start:
					r_per_start[start_triple] = set()

				r_per_start[start_triple].add(Interval(start_triple, end_triple))
		
			else:

				time = t.date.date
				if not time in r_per_start:
					r_per_start[time] = set()
				r_per_start[time].add(t.date)
				
		
		return [i for start in sorted(r_per_start.keys()) for i in r_per_start[start]]

	return []