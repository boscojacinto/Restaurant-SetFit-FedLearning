import os
import re
import sys
import grpc
import time
import json
import torch
import queue
import ctypes
import random
import asyncio
import requests
import threading
import scipy as sp
import numpy as np
import multiprocessing
from ctypes import CDLL
import restaurant_pb2
import restaurant_pb2_grpc
from math import ceil, floor
from subprocess import Popen, PIPE 
from scipy.sparse import coo_matrix
from flwr.client.supernode.app import run_supernode
from restaurant_ai.restaurant_model import AIModel as bot
from restaurant_ai.restaurant_model import CUSTOM_MODEL
import private_set_intersection.python as psi

status_go = None
status_cb = None
ai_client = None
status_client = None
fl_client_1 = None
fl_client_2 = None
psi_client = None
customer_embeddings = None
restaurant_service = None

STATUS_BACKEND_PORT = 0
STATUS_BACKEND_BIN = "./restaurant_status/libs/status-backend"
STATUS_GO_LIB = "./restaurant_status/libs/libstatus.so.0"

AI_MODEL = "swigg1.0-gemma3:1b"
customer_ids = ["0x04c57743b8b39210913de928ae0b8e760d8e220c5539b069527b62f1aa3a49c47ec03188ff32f13916cf28673082a25afdd924d26d768e58e872f3f794365769d4"]
RESTAURANT_UID = "0xdc9e9199cee1b4686864450961848ca39420931d56080baa2ba196283dfc2682"
RESTAURANT_PASSWORD = "swigg@12345"
RESTAURANT_DEVICE = "restaurant-pc-8"
RESTAURANT_NAME = "Restaurant8"
MAX_CUSTOMERS = 10000
CUSTOMER_FEATURES_NUM = 3
CUSTOMER_FEATURES_FILE = 'features_customers.npz'
INITIAL_PROMPT = 'Hello'
FEEDBACK_PROMPT = 'Can you describe your visit to Restaurant 1 in your own words'

class StatusClient:
    def __init__(self, root):
    	global status_go
    	self.lib = status_go
    	self.cb = None
    	self.root = root
    	self.uid = ''
    	self.password = ''
    	self.device_name = ''
    	self.display_name = ''
    	self.wakuv2_nameserver = '8.8.8.8'
    	self.wakuv2_fleet = 'status.prod'
    	self.lib.InitializeApplication.argtypes = [ctypes.c_char_p]
    	self.lib.InitializeApplication.restype = ctypes.c_char_p
    	self.lib.LoginAccount.argtypes = [ctypes.c_char_p]
    	self.lib.LoginAccount.restype = ctypes.c_char_p
    	self.lib.CallRPC.argtypes = [ctypes.c_char_p]
    	self.lib.CallRPC.restype = ctypes.c_char_p
    	self.lib.CreateAccountAndLogin.argtypes = [ctypes.c_char_p]
    	self.lib.CreateAccountAndLogin.restype = ctypes.c_char_p
    	self.lib.CallPrivateRPC.argtypes = [ctypes.c_char_p]
    	self.lib.CallPrivateRPC.restype = ctypes.c_char_p
    	self.thread = None
    	self.message_queue = queue.Queue()
    	print(f"\n========= Initializing Status Messenger ========\n")    	

    def initApp(self, device_name, cb):
    	self.device_name = device_name
    	SIGNAL_CB_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    	status_go.SetSignalEventCallback.argtypes = [ctypes.c_void_p]
    	self.cb = SIGNAL_CB_TYPE(cb)
    	status_go.SetSignalEventCallback(self.cb)
    	data = {"dataDir": self.root, "mixpanelAppId": "", "mixpanelToken": "", "mediaServerEnableTLS": False, "sentryDSN": "", "logDir": self.root, "logEnabled": True, "logLevel": "INFO", "apiLoggingEnabled": True, "metricsEnabled": True, "metricsAddress": "", "deviceName": self.device_name, "rootDataDir": self.root, "wakuV2LightClient": False, "wakuV2EnableMissingMessageVerification": True, "wakuV2EnableStoreConfirmationForMessagesSent": True}
    	payload = json.dumps(data).encode('utf-8')
    	self.lib.InitializeApplication(payload)

    def login(self, uid, password):
    	self.uid = uid
    	self.password = password
    	data = {"password": self.password, "keyUid": self.uid, "wakuV2Nameserver": self.wakuv2_nameserver, "wakuV2Fleet": self.wakuv2_fleet}
    	payload = json.dumps(data).encode('utf-8')
    	self.lib.LoginAccount(payload)

    	time.sleep(2)

    	data = {"method": "wakuext_startMessenger", "params": []}
    	payload = json.dumps(data).encode('utf-8')
    	self.lib.CallRPC(payload)

    def createAccountAndLogin(self, display_name, password):
    	self.display_name = display_name
    	self.password = password
    	data = {'rootDataDir': self.root, 'kdfIterations': 256, 'deviceName': self.device_name, 'displayName': self.display_name, 'password': self.password, "customizationColor":"blue", 'wakuV2Nameserver':self.wakuv2_nameserver, 'wakuV2Fleet':self.wakuv2_fleet}
    	payload = json.dumps(data).encode('utf-8')
    	self.lib.CreateAccountAndLogin(payload)

    def sendContactRequest(self, publicKey, message):
    	data = {"method": "wakuext_sendContactRequest", "params": [{"id": publicKey, "message": message}]}
    	payload = json.dumps(data).encode('utf-8')
    	self.lib.CallPrivateRPC(payload)

    def createOneToOneChat(self, chatId):
    	data = {"method": "chat_createOneToOneChat", "params": ["", chatId, ""]}
    	payload = json.dumps(data).encode('utf-8')
    	self.lib.CallPrivateRPC(payload)

    def deactivateOneToOneChat(self, Id):
    	data = {"method": "wakuext_deactivateChat", "params": [{"id": Id, "preserveHistory": False}]}
    	payload = json.dumps(data).encode('utf-8')
    	self.lib.CallPrivateRPC(payload)

    def sendChatMessage(self, chatId, message):
    	data = {"method": "wakuext_sendChatMessage", "params": [{"chatId": chatId, "text": message, "contentType": 1}]}
    	payload = json.dumps(data).encode('utf-8')
    	self.lib.CallPrivateRPC(payload)

    def on_status_cb(self, signal: str):
    	global ai_client
    	signal = json.loads(signal)
    	if signal["type"] == "node.login":
    		key_uid = signal["event"]["settings"]["key-uid"]
    		public_key = signal["event"]["settings"]["current-user-status"]["publicKey"]
    		print(f"Node Login: uid:{key_uid} publicKey:{public_key}")
    	elif signal["type"] == "message.delivered":
    		print("Message delivered!")
    	elif signal["type"] == "messages.new":
    		try:
    			new_msg = signal["event"]["chats"][0]["lastMessage"]["parsedText"][0]["children"][0]["literal"]
    			c_id = signal["event"]["chats"][0]["lastMessage"]["from"]
    			print(f"New Message received!:{new_msg}, from:{c_id}")
    			if ai_client is not None:
    				ai_client.sendMessage(c_id, new_msg)
    		except KeyError:
    			pass
    	elif signal["type"] == "wakuv2.peerstats":
    		pass
    	return

    def run(self):
    	while True:
    		try:
    			msg = self.message_queue.get(timeout=1)
    			print(f"Queued Message:{msg}")
    			self.ai.sendMessage(msg)
    			self.message_queue.task_done()
    		except queue.Empty:
    			time.sleep(0.2)

    def start(self):
    	global ai_client
    	self.ai = ai_client
    	self.thread = threading.Thread(target=self.run)
    	self.thread.start()

    def queueMessage(self, message):
    	self.message_queue.put(message)

    def stop(self):
    	if self.thread:
    		self.thread.join()

class AIClient:
	def __init__(self, model):
		self.thread = None
		self.initial_prompt = INITIAL_PROMPT
		self.feedback_prompt = FEEDBACK_PROMPT
		self.prompt = None
		self.customer_id = None
		self.started = False
		self.bots = {}
		self.lock = threading.Lock()
		print(f"\n========= Launching AI model {CUSTOM_MODEL} ========\n")

	def run(self, save_embeddings):

		while True:
			with self.lock:
				if self.prompt is not None \
				and self.customer_id is not None \
				and self.bots[self.customer_id] is not None:

					print(f"New prompt: {self.prompt}, from customer: {self.customer_id}")
					_chat = self.bots[self.customer_id].chat

					response = asyncio.run(_chat(self.prompt))
					print(f"Sending Bot's response:{response}")
					_summary = self.bots[self.customer_id].summary

					self.sm.sendChatMessage(self.customer_id, response)

					if _summary is not None:
						_embed = self.bots[self.customer_id].embed
						embeds = asyncio.run(_embed(_summary))
						asyncio.run(save_embeddings(self.customer_id, embeds))
						if asyncio.run(restaurant_feedback(self.customer_id)):
							print("Request customer feedback")
							self.sm.sendChatMessage(self.customer_id, self.feedback_prompt)
						self.bots[self.customer_id] = None

					self.prompt = None
					self.customer_id = None

	def start(self):
		global status_client

		self.sm = status_client
		self.stop_event = threading.Event()
		self.thread = threading.Thread(target=self.run, args=(save_embeddings, ))
		self.started = True 		
		self.thread.start()

	def sendMessage(self, customer_id, message):
		with self.lock:
			try:
				self.bots[customer_id]
				if self.bots[customer_id] == None:
					self.bots[customer_id] = bot()
			except KeyError:
				self.bots[customer_id] = bot()

			self.prompt = message
			self.customer_id = customer_id

	def greet(self, customer_id):
		try:
			self.bots[customer_id]
		except KeyError:
			self.bots[customer_id] = bot()

		_chat = self.bots[customer_id].chat
		
		self.sm.createOneToOneChat(customer_id)

		response = asyncio.run(_chat(self.initial_prompt))
		print(f"Greeting:{response}")
		self.sm.sendChatMessage(customer_id, response)

	def stop(self):
		if self.thread:
			self.stop_event.set()
			self.started = False
			self.thread.join()

class FLClient:
	def __init__(self, i):
		self.started = False
		self.thread = None
		self.id = i
		print(f"\n========= Initializing Flower Client {i} ========\n")

	def run(self, i):
		run_supernode(i)

	def start(self):
		self.thread = threading.Thread(target=self.run, args=(self.id,))
		self.started = True
		self.thread.start()

	def stop(self):
		self.thread.stop()

def start_federated_learning():
	customer_embeds = torch.load('customer_embeddings.pt')
	customer_feats =coo_matrix(customer_embeds)
	sp.sparse.save_npz(CUSTOMER_FEATURES_FILE, customer_feats)

def init_embeddings():
	customer_embeds = torch.zeros(MAX_CUSTOMERS, CUSTOMER_FEATURES_NUM,
								 dtype=torch.float)
	torch.save(customer_embeds, 'customer_embeddings.pt')

async def save_embeddings(customer_id, embeds):
	global status_client

	customer_embeds = torch.load('customer_embeddings.pt')
	torch.manual_seed(42)
	c_id = random.randint(0, MAX_CUSTOMERS - 1)
	customer_embeds[c_id, 2] = torch.tensor(np.linalg.norm(
								embeds[0]), dtype=torch.float)
	torch.save(customer_embeds, 'customer_embeddings.pt')
	customer_feats =coo_matrix(customer_embeds)
	sp.sparse.save_npz(CUSTOMER_FEATURES_FILE, customer_feats)
	status_client.deactivateOneToOneChat(customer_id)

async def restaurant_feedback(customer_id):
	global restaurant_service
	global psi_client

	client_key = bytes(range(32))
	psi_client = psi.client.CreateFromKey(client_key, False)

	try:
		async with grpc.aio.insecure_channel('[::]:50051') as channel:
			restaurant_service = restaurant_pb2_grpc.RestaurantNeighborStub(channel)

			return await restaurant_setup_and_fetch(customer_id)

	except grpc.RpcError as e:
		print(f"RPC error: {e}")
	except Exception as e:
		print(f"Restaurant feeback error: {e}")

async def restaurant_setup_and_fetch(customer_id):
	global psi_client

	setup_request = restaurant_pb2.SetupRequest(num_customers=1)
	setup_reply = await restaurant_service.Setup(setup_request)

	items = [customer_id]
	request = psi.Request()
	request.ParseFromString(psi_client.CreateRequest(
							items).SerializeToString())

	customer_request = restaurant_pb2.CustomerRequest(request=request)
	customer_reply = await restaurant_service.Fetch(request=customer_request)

	intersection = psi_client.GetIntersectionSize(setup_reply.setup,
										customer_reply.response)
	return intersection

def main():
	global status_go
	global ai_client
	global fl_client_1
	global fl_client_2
	global status_client
	global customer_ids
	global AI_MODEL
	global RESTAURANT_UID
	global RESTAURANT_PASSWORD
	global RESTAURANT_DEVICE
	global RESTAURANT_NAME
	global STATUS_BACKEND_BIN

	try:
		status_backend = Popen([STATUS_BACKEND_BIN, "--address", "127.0.0.1:0"])
	except OSError as e:
		print(f"Error: status_backend failed to start:{e}.")

	status_go = CDLL(STATUS_GO_LIB)

	fl_client_1 = FLClient(1)
	fl_client_1.start()
	time.sleep(0.5)

	fl_client_2 = FLClient(2)
	fl_client_2.start()
	time.sleep(0.5)

	status_client = StatusClient(root="./")
	time.sleep(0.5)

	ai_client = AIClient(AI_MODEL)

	init_embeddings()

	status_client.initApp(RESTAURANT_PASSWORD, cb=status_client.on_status_cb)
	time.sleep(0.5)

	# status_client.createAccountAndLogin(RESTAURANT_NAME, RESTAURANT_PASSWORD)
	# time.sleep(0.5)

	status_client.login(RESTAURANT_UID, RESTAURANT_PASSWORD)
	time.sleep(0.5)

	# status_client.sendContactRequest(customer_ids[0], "Hello! This is your restaurant Bot")
	# time.sleep(0.5)

	status_client.start()
	time.sleep(0.5)
	
	ai_client.start()

	ai_client.greet(customer_ids[0])

	try:
		while True:
			time.sleep(0.1)
	except KeyboardInterrupt:
		fl_client_1.stop()
		fl_client_2.stop()
		status_client.stop()
		ai_client.stop()
		status_backend.terminate()

if __name__ == '__main__':
	main()