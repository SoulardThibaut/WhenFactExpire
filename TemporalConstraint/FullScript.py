import TimePackage as tp
import sys 
from tqdm import tqdm
import numpy as np
import traceback
import pandas as pd
from functools import reduce
import os 
import multiprocessing as mp 
from subprocess import DEVNULL, STDOUT, check_call

temporal_granularity = "D"
today = np.datetime64("2024-12-31", temporal_granularity)



def processing_date_unknown_allowed(date_raw, unknown="None") -> np.datetime64:
	if date_raw == unknown:
		return None
	else:
		return np.datetime64(date_raw, temporal_granularity)

# Find the relation that appears globally
def find_global_appiration(relation_seen, entities):

	first_appearance_of_r = {}
	ent_per_r = {}

	for r in relation_seen:
		first_appearance_of_r[r] = {}
		ent_per_r[r] = set()

		for entity in entities.values():

			timeline_r = entity.get_triples_with_r(r)
			if timeline_r != None:
				ent_per_r[r].add(entity)
				first_date = tp.ordered_timeline_of_r_mono_value_per_int(entity, r)[0][1]
				if not first_date in first_appearance_of_r[r]:
					first_appearance_of_r[r][first_date] = 0
				first_appearance_of_r[r][first_date] += 1

	mini_appearance = 10
	threshold_global = 0.95

	global_relation = set()
	
	for r in first_appearance_of_r:

		nb_apparition = 0
		date_first = np.datetime64("2050", "Y")

		for date in first_appearance_of_r[r]:
			
			if date_first > date:
				nb_apparition = first_appearance_of_r[r][date]
				date_first = date

		if nb_apparition != 0:

			total_ent_alive_at_the_moment = 0

			for ent in ent_per_r[r]:
				if ent.get_lifespan().get_start() <= date_first:
					total_ent_alive_at_the_moment+=1

		if nb_apparition > mini_appearance : 
			if nb_apparition / total_ent_alive_at_the_moment > threshold_global:
				global_relation.add(r)

	return global_relation

def find_multivaluation_temporal(entities, type_relations):
	multi_r = set()
	multi_r_count_kept = {}
	count_per_r = {}
	count_v_per_r = {}

	for ent in entities.values():
		
		for r in ent.triples_per_r:

			if not r in count_v_per_r:
				count_v_per_r[r] = {}
				if not r in multi_r_count_kept:
					multi_r_count_kept[r] = 0
				multi_r_count_kept[r] += 1 
			
			if not r in count_per_r:
				count_per_r[r] = 0
				multi_r_count_kept[r] = 0

			count_per_r[r] += 1
		
			seq = tp.TimeSequence(tp.ordered_time_sequence_first_start(ent, r, temporal_granularity=temporal_granularity))
			if seq.multi_valuation_temporal:
				multi_r_count_kept[r] += 1 

			for t in ent.triples_per_r[r]:
				v = t.value

				if not v in count_v_per_r[r]:
					count_v_per_r[r][v] = 0

				count_v_per_r[r][v] += 1

	for r in count_per_r:
		if r == -3:
			print(multi_r_count_kept[r] ,count_per_r[r],(1-seuil))
		if multi_r_count_kept[r]  >= count_per_r[r]* (1-seuil):
			multi_r.add(r)

	rxv_allowed = set()
	for r in count_v_per_r:
		if r < 0 or type_relations[r] == "OP":
			for v in count_v_per_r[r]:
				if count_v_per_r[r][v] > mini_entity:
					rxv_allowed.add((r,v))

	for ent in entities.values():
		ent.generate_triples_per_r_and_rxv(rxv_allowed)

	return multi_r

def generate_rules(couple, property, error_percent, coverage):

	first = None
	first_precision = None
	
	if couple[0][0] == "(":
		first, first_precision = couple[0][1:-1].split(", ")
		first, first_precision = int(first), int(first_precision)
	else:
		first = int(couple[0])

	second = None
	second_precision = None
	if couple[1][0] == "(":
		second, second_precision = couple[1][1:-1].split(", ")
		second, second_precision = int(second), int(second_precision)
	else:
		second = int(couple[1])

	if property[0] == "A":
		return tp.TemporalRule(first, first_precision,\
								property[2:-2],\
								second, second_precision,\
								error_percent, coverage)
	else:    
		return tp.TemporalRule(second, second_precision,\
								property[2:-2],\
								first, first_precision,\
								error_percent, coverage)
	
def find_rules_only_r(entities, multivaluation_relations, global_relation):

	comparison_per_couple_of_r = {}

	for ent in entities.values():
		# print(ent)
		
		r = list(set(ent.triples_per_r.keys()).difference(global_relation).difference(multivaluation_relations))
		
		for i, r_1 in enumerate(r):
			sequence_r_1 = tp.TimeSequence(tp.ordered_time_sequence_first_start(ent, r_1, temporal_granularity=temporal_granularity))
			if not sequence_r_1.multi_valuation_temporal:
				for r_2 in r[i+1:]:
					sequence_r_2 = tp.TimeSequence(tp.ordered_time_sequence_first_start(ent, r_2, temporal_granularity=temporal_granularity))
					if not sequence_r_2.multi_valuation_temporal:
						relations_between_1_2 = tp.TimeSequenceRelation(r_1, r_2, sequence_r_1, sequence_r_2)
						name = relations_between_1_2.get_name()
						if not name in comparison_per_couple_of_r:
							comparison_per_couple_of_r[name] = set()
						comparison_per_couple_of_r[name].add(relations_between_1_2)
	
	props_per_couple = {}
	for r_1, r_2 in comparison_per_couple_of_r:
		props_per_couple[(r_1, r_2)] = {"total": len(comparison_per_couple_of_r[(r_1, r_2)])}
		for tsr in comparison_per_couple_of_r[(r_1, r_2)]:
			for props_r_1_o_r_2 in tsr.A_o_B:
				name_props = "A "+props_r_1_o_r_2+" B"
				if not name_props in props_per_couple[(r_1, r_2)]:
					props_per_couple[(r_1, r_2)][name_props] = 0
				props_per_couple[(r_1, r_2)][name_props] += 1 

			for props_r_1_o_r_2 in tsr.B_o_A:
				name_props = "B "+props_r_1_o_r_2+" A"
				if not name_props in props_per_couple[(r_1, r_2)]:
					props_per_couple[(r_1, r_2)][name_props] = 0
				props_per_couple[(r_1, r_2)][name_props] += 1 

	rules = set()

	for couple in props_per_couple:
		total = props_per_couple[couple]["total"]

		if total > mini_entity:
			for property in set(props_per_couple[couple].keys()).difference(['total']):
				if props_per_couple[couple][property] > total*seuil:
					a = generate_rules(couple, property, props_per_couple[couple][property]/total, total)
					rules.add(a)
	return rules

def verify_comparison_allowed(r_1, r_2):
	if (type(r_1) != tuple) and (type(r_2) != tuple):
		return r_1 != r_2
	elif (type(r_1) != tuple):
		return r_1 != r_2[0]
	elif (type(r_2) != tuple):
		return r_1[0] != r_2
	else:
		return (r_1[0] != r_2[0]) or (r_1[1] != r_2[1])

def find_rules_r_and_rxv(entities, multivaluation_relations, global_relation):
	comparison_per_couple_of_r = {}

	for ent in entities.values():

		r = list(set(ent.triples_per_r_and_rxv.keys()).difference(global_relation).difference(multivaluation_relations))

		for i, r_1 in enumerate(r):
			sequence_r_1 = tp.TimeSequence(tp.ordered_time_sequence_first_start_with_rxv(ent, r_1, temporal_granularity=temporal_granularity))
			if not sequence_r_1.multi_valuation_temporal:
				for r_2 in r[i+1:]:
					if verify_comparison_allowed(r_1, r_2):
						sequence_r_2 = tp.TimeSequence(tp.ordered_time_sequence_first_start_with_rxv(ent, r_2, temporal_granularity=temporal_granularity))
						
						if not sequence_r_2.multi_valuation_temporal:   
							relations_between_1_2 = tp.TimeSequenceRelation(r_1, r_2, sequence_r_1, sequence_r_2)
							name = relations_between_1_2.get_name()
							if not name in comparison_per_couple_of_r:
								comparison_per_couple_of_r[name] = set()
							comparison_per_couple_of_r[name].add(relations_between_1_2)

	props_per_couple = {}
	for r_1, r_2 in comparison_per_couple_of_r:
		props_per_couple[(r_1, r_2)] = {"total": len(comparison_per_couple_of_r[(r_1, r_2)])}
		for tsr in comparison_per_couple_of_r[(r_1, r_2)]:
			for props_r_1_o_r_2 in tsr.A_o_B:
				name_props = "A "+props_r_1_o_r_2+" B"
				if not name_props in props_per_couple[(r_1, r_2)]:
					props_per_couple[(r_1, r_2)][name_props] = 0
				props_per_couple[(r_1, r_2)][name_props] += 1 

			for props_r_1_o_r_2 in tsr.B_o_A:
				name_props = "B "+props_r_1_o_r_2+" A"
				if not name_props in props_per_couple[(r_1, r_2)]:
					props_per_couple[(r_1, r_2)][name_props] = 0
				props_per_couple[(r_1, r_2)][name_props] += 1 
	
	rules = set()
	for couple in props_per_couple:
		total = props_per_couple[couple]["total"]

		if total > mini_entity:
			for property in set(props_per_couple[couple].keys()).difference(['total']):
				if props_per_couple[couple][property] > total*seuil:
					rules.add(generate_rules(couple, property, props_per_couple[couple][property]/total, total))
					
	return rules

def index_rules(rules):
	i_rules = dict()
	for rule in rules:
		a = rule.get_a()
		if a not in i_rules:
			i_rules[a] = set()
		i_rules[a].add(rule)
		b = rule.get_b()
		if b not in i_rules:
			i_rules[b] = set()
		i_rules[b].add(rule)
	return i_rules

def function_subprocess(works:mp.Queue, entities:dict, rule_indexed_per_class, classes_per_entity, threshold, f_str, print_every:int=0, id_child=0) :
	with open(f_str, "w", encoding="UTF-8") as f:
		while True:
			try:
				if print_every:
					size = works.qsize()
					if size and size%print_every==0:
						print(f"Still {size} facts in the Queue.")
				id, triple = works.get(timeout=10)
				
				f.write(f"{id}\t{triple}\t")
				
				if  (triple.head not in entities) and (triple.value not in entities):
					f.write(f"2\tNo data on the head\t_\t_\n")
				else:


					#Followed, not Followed, Unknown
					count_rules = [0,0,0]

					#Could work on 
					sequences = [True, True]
					
					if triple.head in entities:
						entity = entities[triple.head]
						classes_entity = classes_per_entity[triple.head]
						entity.add_triple(triple)
						checked = set()

						for class_entity in classes_entity:
									
							if class_entity in rule_indexed_per_class:
								if triple.relation in rule_indexed_per_class[class_entity]:
									for rule in rule_indexed_per_class[class_entity][triple.relation]:
										if (rule.get_a(), rule.get_r(), rule.get_b()) not in checked:
											checked.add((rule.get_a(), rule.get_r(), rule.get_b()))
											ts_a = tp.TimeSequence(tp.ordered_time_sequence_first_start(entity, rule.get_a(), temporal_granularity=temporal_granularity))
											ts_b = tp.TimeSequence(tp.ordered_time_sequence_first_start(entity, rule.get_b(), temporal_granularity=temporal_granularity))
											if (not ts_a.multi_valuation_temporal) and (not ts_b.multi_valuation_temporal):
												if (len(ts_a.intervals) != 0) and (len(ts_b.intervals) != 0):
													tsr = tp.TimeSequenceRelation(rule.get_a(), rule.get_b(), ts_a, ts_b, rule)
													if tsr.verified:
														count_rules[0]+=1
													else:
														count_rules[1]+=1
												else:
													count_rules[2]+=1
											else:
												sequences[0] = False
						
						entity.remove_triple(triple)

					if triple.value in entities:
						entity_object = entities[triple.value]

						if triple.value in classes_per_entity:

							classes_entity_object = classes_per_entity[triple.value]
							
							triple_inv = tp.Triple(triple.value, triple.relation*-1-1, triple.head, triple.date)
							entity_object.add_triple(triple_inv)
							checked = set()

							for class_entity_object in classes_entity_object:
					
								if class_entity_object in rule_indexed_per_class:
									if triple_inv.relation in rule_indexed_per_class[class_entity_object]:
										for rule in rule_indexed_per_class[class_entity_object][triple_inv.relation]:
											if (rule.get_a(), rule.get_r(), rule.get_b()) not in checked:
												checked.add((rule.get_a(), rule.get_r(), rule.get_b()))
												ts_a = tp.TimeSequence(tp.ordered_time_sequence_first_start(entity_object, rule.get_a(), temporal_granularity=temporal_granularity))
												ts_b = tp.TimeSequence(tp.ordered_time_sequence_first_start(entity_object, rule.get_b(), temporal_granularity=temporal_granularity))
												if (not ts_a.multi_valuation_temporal) and (not ts_b.multi_valuation_temporal):
													if (len(ts_a.intervals) != 0) and (len(ts_b.intervals) != 0):
														tsr = tp.TimeSequenceRelation(rule.get_a(), rule.get_b(), ts_a, ts_b, rule)
														if tsr.verified:
															count_rules[0]+=1
														else:
															count_rules[1]+=1
													else:
														count_rules[2]+=1
												else:
													sequences[0] = False


									ts = tp.TimeSequence(tp.ordered_time_sequence_first_start_with_rxv(entity_object, (triple_inv.relation,triple_inv.value), temporal_granularity=temporal_granularity))
									if (triple_inv.relation, triple_inv.value) in rule_indexed_per_class[class_entity_object]:
										# print("hEllo world")
										for rule in rule_indexed_per_class[class_entity_object][(triple_inv.relation, triple_inv.value)]:
											ts_a = tp.TimeSequence(tp.ordered_time_sequence_first_start_with_rxv(entity_object, rule.get_a(), temporal_granularity=temporal_granularity))
											ts_b = tp.TimeSequence(tp.ordered_time_sequence_first_start_with_rxv(entity_object, rule.get_b(), temporal_granularity=temporal_granularity))
											if (not ts_a.multi_valuation_temporal) and (not ts_b.multi_valuation_temporal):
												if (len(ts_a.intervals) != 0) and (len(ts_b.intervals) != 0):
													tsr = tp.TimeSequenceRelation(rule.get_a(), rule.get_b(), ts_a, ts_b, rule)
													if tsr.verified:
														count_rules[0]+=1
													else:
														count_rules[1]+=1
													
												else:
													count_rules[2]+=1
											else:
												sequences[1] = False
												
							entity_object.remove_triple(triple_inv)
					if (not sequences[0]) & (not sequences[1]) & (count_rules[0] + count_rules[1] == 0):
						f.write(f"4\tBoth sequences were multi-valued\t_\t_\n")
						
					elif count_rules[0] + count_rules[1] == 0:
						f.write(f"3\tNo rules could be used\t_\t_\n")
							

					elif count_rules[0] / (count_rules[0]+count_rules[1]) > threshold :
						f.write(f"0\tTrue\t{count_rules[0] / (count_rules[0]+count_rules[1])}\t{(count_rules[0]+count_rules[1])}\n")

					# At least one rule has refuted the thing 
					else :
						f.write(f"1\tFalse\t{count_rules[0] / (count_rules[0]+count_rules[1])}\t{(count_rules[0]+count_rules[1])}\n")
			except :
				#print(e, flush=True)
				print(f"{id_child} done", flush=True)
				return None

def load_classes(path, ents_to_id):
	ents_per_classes = dict()
	with open(path, "r", encoding="UTF-8") as f_r:
		line = f_r.readline()
		while line != "":
			entity, classes = line[:-1].split("\t")
			entity = int(entity)
			for classe in {int(c) for c in classes.split(" ")}:
				if classe not in ents_per_classes:
					ents_per_classes[classe] = set()
				ents_per_classes[classe].add(entity)
			line = f_r.readline()
	return ents_per_classes

def load_ids(path):
	instance_to_id = dict()
	id_to_instance = dict()
	with open(path, "r", encoding="UTF-8") as f_r:
		line = f_r.readline()
		while line != "":
			instance, id = line[:-1].split("\t")
			instance_to_id[instance] = int(id)
			id_to_instance[int(id)] = instance
			line = f_r.readline()
	return instance_to_id, id_to_instance

def load_graph(path, path_gt, is_object:bool=True):
	graph = set()
	with open(path, "r", encoding="UTF-8") as f_r:
		with open(path_gt, "r", encoding="UTF-8") as f_r_gt:
			line = f_r.readline()
			line_gt = f_r_gt.readline()
			try:
				while line != "":
					if line_gt[:-1] == "True":
						elts = line[:-1].split("\t")
						if len(elts) == 4: # Singular point
							s,p,o,t = elts
						else:
							s,p,o,t = elts[0], elts[1], elts[2], (elts[3], elts[4])
						s, p = int(s), int(p)
						if is_object:
							o = int(o)
						else:
							o = o
						
						if type(t)==tuple:
							
							start, end = t
						else:
							
							start = t
							end = str(processing_date_unknown_allowed(start)+np.timedelta64(1,temporal_granularity))

						start_processed = processing_date_unknown_allowed(start)
						end_processed = processing_date_unknown_allowed(end)
						if start_processed == end_processed:
							end_processed = end_processed+np.timedelta64(1, temporal_granularity)
						elif start_processed and end_processed and (start_processed > end_processed):
							print(start_processed, end_processed)

						graph.add(tp.Triple(s, p, o,
										tp.Interval(start_processed, end_processed),is_object))
					line = f_r.readline()
					line_gt = f_r_gt.readline()
			except:
				print(line)
	return graph

def load_graph_test(path, path_gt):
	graph_pos, graph_neg = list(), list()
	with open(path, "r", encoding="UTF-8") as f_r:
		with open(path_gt, "r", encoding="UTF-8") as f_r_gt:
			line = f_r.readline()
			line_gt = f_r_gt.readline()
			while line != "":
				elts = line[:-1].split("\t")
				if len(elts) == 4: # Singular point
					s,p,o,t = elts
				else:
					s,p,o,t = elts[0], elts[1], elts[2], (elts[3], elts[4])
				s, p, o = int(s), int(p), int(o)
				
				if type(t)==tuple:
					
					start, end = t
				else:
					
					start = t
					end = str(processing_date_unknown_allowed(start)+np.timedelta64(1,temporal_granularity))

				if  line_gt[:-1] == "True":
					graph_pos.append(tp.Triple(s, p, o,
									tp.Interval(processing_date_unknown_allowed(start),
												processing_date_unknown_allowed(end))))
				else:
					graph_neg.append(tp.Triple(s, p, o,
									tp.Interval(processing_date_unknown_allowed(start),
												processing_date_unknown_allowed(end))))
				line = f_r.readline()
				line_gt = f_r_gt.readline()

	return graph_pos, graph_neg

def index_graph(graph) -> dict[str, tp.Entity]:
	indexed_graph = dict()
	for f in graph:
		s,o = f.head, f.value
		if s not in indexed_graph:
			indexed_graph[s] = tp.Entity(s, 
								today=today,
								granularity=temporal_granularity)
		indexed_graph[s].add_triple(f)

		if f.is_object:
			if o not in indexed_graph:
				indexed_graph[o] = tp.Entity(o, 
								today=today,
								granularity=temporal_granularity)
			indexed_graph[o].add_triple(tp.Triple(
				f.value,
				f.relation*-1-1,
				f.head,
				f.date, 
				True))

	return indexed_graph

def add_unknown_entities_to_class(ents_per_classes:dict, ents_to_id):
	ents_per_classes["Unknown"] = set()
	for ent in ents_to_id:
		if ent[:len("Unkonwn_b")] == "Unkonwn_b":
			ents_per_classes["Unknown"].add(ents_to_id[ent])
	return ents_per_classes

def add_untyped_entities_to_class(ents_per_classes:dict, id_to_ents):
	all_entities_typed = set()
	for i in [v for v in ents_per_classes.values()]:
		all_entities_typed.update(i)

	ents_per_classes["Untyped"] = set(id_to_ents).difference(all_entities_typed)
	return ents_per_classes

def create_folder(directory:str):
	if not os.path.exists(directory):
		os.makedirs(directory)

def return_the_type(values):
	if values[True] > values[False]:
		return False
	else:
		return True
	
def genereate_all_temporal_sequence(entities:dict[str, tp.Entity]) -> dict[str, dict[str, list]]:
	res = dict()
	for e in tqdm(entities):
		res[e] = dict()
		for r in entities[e].triples_per_r:
			res[e][r] = tp.ordered_time_sequence_first_start(entities[e], r, temporal_granularity=temporal_granularity)

def find_behavior_per_entity(entities):

	behavior_per_couple_of_r_per_entity = {}

	for ent_name in tqdm(entities.keys()):
		# print(ent)
		behavior_per_couple_of_r_per_entity[ent_name] = dict()
		ent = entities[ent_name]
		r = list(set(ent.triples_per_r.keys()))
		
		for i, r_1 in enumerate(r):
			sequence_r_1 = tp.TimeSequence(tp.ordered_time_sequence_first_start(ent, r_1, temporal_granularity=temporal_granularity))
			for r_2 in r[i+1:]:
				sequence_r_2 = tp.TimeSequence(tp.ordered_time_sequence_first_start(ent, r_2, temporal_granularity=temporal_granularity))
				relations_between_1_2 = tp.TimeSequenceRelation(r_1, r_2, sequence_r_1, sequence_r_2)
				name = relations_between_1_2.get_name()
				if relations_between_1_2.at_least_one_multi:
					behavior_per_couple_of_r_per_entity[ent_name][name] = (True,set(),set())
				else:
					behavior_per_couple_of_r_per_entity[ent_name][name] = (False,relations_between_1_2.A_o_B,relations_between_1_2.B_o_A)

	
	return behavior_per_couple_of_r_per_entity

def find_behavior_per_entity_with_value(entities, to_check):

	behavior_per_couple_of_r_per_entity = {}

	for ent_name in tqdm(entities.keys()):
		# print(ent)
		behavior_per_couple_of_r_per_entity[ent_name] = dict()
		ent = entities[ent_name]
		r = list(set(ent.triples_per_r_and_rxv.keys()).intersection(to_check))
		
		for i, r_1 in enumerate(r):
			sequence_r_1 = tp.TimeSequence(tp.ordered_time_sequence_first_start_with_rxv(ent, r_1, temporal_granularity=temporal_granularity))
			for r_2 in r[i+1:]:
				sequence_r_2 = tp.TimeSequence(tp.ordered_time_sequence_first_start_with_rxv(ent, r_2, temporal_granularity=temporal_granularity))
				relations_between_1_2 = tp.TimeSequenceRelation(r_1, r_2, sequence_r_1, sequence_r_2)
				name = relations_between_1_2.get_name()
				if relations_between_1_2.at_least_one_multi:
					behavior_per_couple_of_r_per_entity[ent_name][name] = (True,set(),set())
				else:
					behavior_per_couple_of_r_per_entity[ent_name][name] = (False,relations_between_1_2.A_o_B,relations_between_1_2.B_o_A)

	
	return behavior_per_couple_of_r_per_entity

def reduce_behaviors(behavior_per_couple_of_r_per_entity):
	
	behavior_per_couple = {}
	for ent in behavior_per_couple_of_r_per_entity:
		for r_1, r_2 in behavior_per_couple_of_r_per_entity[ent]:
			if (r_1, r_2) not in behavior_per_couple:
				behavior_per_couple[(r_1, r_2)] = {"total": 0, "multivalued":0}
			behavior_per_couple[(r_1, r_2)]["total"] += 1
			is_multivalued, A_o_B, B_o_A =  behavior_per_couple_of_r_per_entity[ent][(r_1, r_2)]
			if not is_multivalued:
				for props_r_1_o_r_2 in A_o_B:
					name_props = "A "+props_r_1_o_r_2+" B"
					if not name_props in behavior_per_couple[(r_1, r_2)]:
						behavior_per_couple[(r_1, r_2)][name_props] = 0
					behavior_per_couple[(r_1, r_2)][name_props]+=1

				for props_r_1_o_r_2 in B_o_A:
					name_props = "B "+props_r_1_o_r_2+" A"
					if not name_props in behavior_per_couple[(r_1, r_2)]:
						behavior_per_couple[(r_1, r_2)][name_props] = 0
					behavior_per_couple[(r_1, r_2)][name_props]+=1
			
			else:
				behavior_per_couple[(r_1, r_2)]["multivalued"] += 1
	
	return behavior_per_couple

def select_final_rules(behavior_per_couple, 
					   threshold_multi_valued:float, 
					   threshold:float,
					   mini_entity_abs:int):
	rules = set()

	for couple in behavior_per_couple:
		total = behavior_per_couple[couple]["total"]
		mini_entity = max(1,total*(int(mini_entity_abs)/100)) ### NOT SURE IF TOTAL or LEN(Entities) not in the parameters but can be easily added

		if behavior_per_couple[couple]["multivalued"]/behavior_per_couple[couple]["total"] < threshold_multi_valued:


			if total > mini_entity:
				for property in set(behavior_per_couple[couple].keys()).difference(['total', "multivalued"]):
					if behavior_per_couple[couple][property] > total*threshold:
						a = generate_rules(couple, property, behavior_per_couple[couple][property]/total, total)
						rules.add(a)
	
	return rules

root_output_path = "./Outputs_work/"
create_folder(root_output_path)
with open(f"{root_output_path}Res.txt", "w", encoding="UTF-8") as f_out_res : 

	for type_data in ["TR", "FD"]:
		for granularity in ["Y", "D"]:
			for name in ["Extra_Small", "Small", "Medium", "Large"][-1:]:
				path = f"./../Retrieve_Data/Data/{type_data}_{granularity}/{name}/"

				ents_to_id, id_to_ents = load_ids(f"{path}Entity2ID.txt")
				rels_to_id, id_to_rels = load_ids(f"{path}Relation2ID.txt")
				class_to_id, id_to_class = load_ids(f"{path}Class2ID.txt")

				ents_per_classes = load_classes(f"{path}ClassPerEntityExtended.txt", ents_to_id)
				ents_per_classes = add_unknown_entities_to_class(ents_per_classes=ents_per_classes, ents_to_id=ents_to_id)
				ents_per_classes = add_untyped_entities_to_class(ents_per_classes=ents_per_classes, id_to_ents=id_to_ents)

				graph = load_graph(f"{path}OP_train.txt", f"{path}OP_train.gt", True)
				graph.update(load_graph(f"{path}DP_train.txt", f"{path}DP_train.gt", False))
				i_graph = index_graph(graph)

				r_type = {}
				for fact in graph:
					if fact.relation not in r_type:
						r_type[fact.relation] = {True:0, False:0}
					r_type[fact.relation][fact.is_object] += 1

				for r in [r  for r in r_type if (r_type[r][True] != 0) and (r_type[r][False] != 0)]:
					print(r, r_type[r])

				type_relations = {r:"OP" if r_type[r][True]!=0 else "DP" for r in r_type }

				stranges_r = [r  for r in r_type if (r_type[r][True] != 0) and (r_type[r][False] != 0)]
				for fact in graph:
					if fact.relation in stranges_r and fact.is_object == return_the_type(r_type[r]):
						print(fact)
						
				keep_track = {}
				for i in i_graph:
					ent = i_graph[i]
					for rxv in ent.triples_per_r_and_rxv:
						if rxv not in keep_track:
							keep_track[rxv] = set()
						keep_track[rxv].add(i)

				to_check = set()
				#for rxv in tqdm(keep_track):
				#	if sum({len(keep_track[rxv].intersection(ents_per_classes[c]))/len(ents_per_classes[c]) for c in ents_per_classes}) > 0:
				#		to_check.add(rxv)
				for rxv in tqdm(keep_track):
					if len(keep_track[rxv]) > 3:
						to_check.add(rxv)

				rules_per_c = dict()
				i_rules_per_c = dict()

				#rules_rxv_per_c = dict()
				#i_rules_rxv_per_c = dict()

				percentage_entity = 5
				mini_entity_abs = 10
				threshold = 0.9
				threshold_multivaluation = 0.05
							
				behavior_per_entity_and_relations = find_behavior_per_entity(i_graph)

				for c in  tqdm(ents_per_classes):
					behavior_per_entity_and_relations_of_class = {e:behavior_per_entity_and_relations[e] for e in ents_per_classes[c] if e in behavior_per_entity_and_relations }


					behaviors_reduced = reduce_behaviors(behavior_per_entity_and_relations_of_class)
					rules_r = select_final_rules(behaviors_reduced, threshold_multivaluation, threshold, mini_entity_abs)

					rules_clean = tp.remove_useless_complex_rules(rules_r)

					rules_per_c[c] = rules_clean
					i_rules_per_c[c] = index_rules(rules_clean)

					#rules_r_and_rxv = find_rules_r_and_rxv(entities, multivaluation_relations, global_relation)
					#rulesr_and_rxv_clean = tp.remove_useless_complex_rules(rules_r_and_rxv)
					
					#rules_rxv_per_c[c] = rulesr_and_rxv_clean
					#i_rules_rxv_per_c[c] = index_rules(rulesr_and_rxv_clean)

				graph_test_pos, graph_test_neg = load_graph_test(f"{path}OP_test.txt", f"{path}/OP_test.gt")

				classes_per_ent = dict()
				for c in ents_per_classes:
					for e in ents_per_classes[c]:
						if e not in classes_per_ent:
							classes_per_ent[e]=set()
						classes_per_ent[e].add(c)

				threshold_validation = 0.9


				output_path = f"./Outputs_work/{type_data}_{granularity}_{name}/"
				create_folder(output_path)

				nb_process = 5
				print_percent = 100
				print("Verify facts")
				with mp.Manager() as manager:

					works = mp.Queue()
					for i, fact in enumerate(graph_test_pos):
						# print(i, fact)
						works.put((i, fact))

					size_queue = works.qsize()
					processes = []
					print(works.qsize())
					for id in range(nb_process):
						p = mp.Process(target=function_subprocess, args=(works, 
																i_graph,
																i_rules_per_c, 
																classes_per_ent, 
																threshold_validation, 
																f"{output_path}True_output_{id}.txt",
																int(size_queue/print_percent),
																id))
						processes.append(p)
						p.start()

					for j in range(len(processes)):
						processes[j].join()

					cmd = "cat "
					for id in range(nb_process):
						cmd += f"{output_path}True_output_{id}.txt "
					cmd += f"> {output_path}True_output.txt"
					check_call(cmd, shell=True, stdout=DEVNULL, stderr=STDOUT)

					for id in range(nb_process):
						cmd = f"rm {output_path}True_output_{id}.txt "
						check_call(cmd, shell=True, stdout=DEVNULL, stderr=STDOUT)

					works = mp.Queue()
					for i, fact in enumerate(graph_test_neg):
						# print(i, fact)
						works.put((i, fact))

					size_queue = works.qsize()
					processes = []
					for id in range(nb_process):
						p = mp.Process(target=function_subprocess, args=(works, 
																i_graph,
																i_rules_per_c, 
																classes_per_ent, 
																threshold_validation, 
																f"{output_path}False_output_{id}.txt",
																int(size_queue/print_percent),
																id))
						processes.append(p)
						p.start()

					for j in range(len(processes)):
						processes[j].join()

					cmd = "cat "
					for id in range(nb_process):
						cmd += f"{output_path}False_output_{id}.txt "
					cmd += f"> {output_path}False_output.txt"
					check_call(cmd, shell=True, stdout=DEVNULL, stderr=STDOUT)

					for id in range(nb_process):
						cmd = f"rm {output_path}False_output_{id}.txt "
						check_call(cmd, shell=True, stdout=DEVNULL, stderr=STDOUT)


				cpt = 0
				cpt_predicted = 0
				cpt_predicted_right = 0

				
				with open(f"{output_path}False_output.txt", "r", encoding="UTF-8") as f_r:
					line = f_r.readline()

					while line != "":
						cpt+=1

						dec = int(line.split("\t")[2])
						cpt += 1
						if dec in {0,1}:
							cpt_predicted+=1
							if dec == 1 :
								cpt_predicted_right+=1

						line = f_r.readline()
				with open(f"{output_path}True_output.txt", "r", encoding="UTF-8") as f_r:
					line = f_r.readline()

					while line != "":
						cpt+=1

						dec = int(line.split("\t")[2])
						cpt += 1
						if (dec) in {0,1}:
							cpt_predicted+=1
							if dec == 0 :
								cpt_predicted_right+=1

						line = f_r.readline()

				f_out_res.write(f"{type_data}, {name}, {granularity}, {cpt}, {cpt_predicted}, {cpt_predicted_right}\n")