db = db.getSiblingDB('quantum_dashboard');

db.createCollection("users");
db.createCollection("temporal_capsules");
db.createCollection("quantum_circuits");
db.createCollection("quantum_measurements");
db.createCollection("conversations");
db.createCollection("chat_messages");
db.createCollection("friendships");
db.createCollection("capsule_permissions");
db.createCollection("quantum_vault_items");
db.createCollection("system_notifications");
db.createCollection("configuration_settings");

db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "username": 1 }, { unique: true });
db.temporal_capsules.createIndex({ "user_id": 1, "created_at": -1 });
db.temporal_capsules.createIndex({ "unlock_date": 1 });
db.conversations.createIndex({ "participants": 1 });
db.chat_messages.createIndex({ "conversation_id": 1, "timestamp": -1 });

print("MongoDB initialized for Quantum Dashboard!");
