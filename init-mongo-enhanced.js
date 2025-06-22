db = db.getSiblingDB('quantum_dashboard');

// Drop existing collections if they exist (for development)
const collections = [
    'users', 'temporal_capsules', 'quantum_circuits', 'quantum_measurements',
    'quantum_connections', 'quantum_messages', 'quantum_images', 'user_sessions',
    'quantum_experiments', 'system_notifications', 'quantum_vault_items',
    'activity_logs', 'quantum_states', 'configuration_settings',
    'conversations', 'chat_messages', 'friendships', 'capsule_permissions'
];

collections.forEach(collection => {
    db[collection].drop();
    print(`Dropped collection: ${collection}`);
});

// Create collections with enhanced validation schemas
db.createCollection("users", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["username", "email", "hashed_password"],
            properties: {
                username: { bsonType: "string", minLength: 3, maxLength: 30 },
                email: { bsonType: "string", pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$" },
                hashed_password: { bsonType: "string" },
                full_name: { bsonType: "string", maxLength: 100 },
                quantum_level: { bsonType: "int", minimum: 1, maximum: 100 },
                is_active: { bsonType: "bool" },
                created_at: { bsonType: "date" },
                last_login: { bsonType: "date" },
                avatar_path: { bsonType: "string" }
            }
        }
    }
});

db.createCollection("temporal_capsules", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "title", "unlock_date", "status", "capsule_type"],
            properties: {
                user_id: { bsonType: "string" },
                title: { bsonType: "string", minLength: 1, maxLength: 200 },
                description: { bsonType: "string", maxLength: 1000 },
                capsule_type: { enum: ["memory", "message", "image", "quantum_state"] },
                content: { bsonType: "object" },
                unlock_date: { bsonType: "date" },
                created_at: { bsonType: "date" },
                status: { enum: ["locked", "unlocked", "expired"] },
                tags: { bsonType: "array", items: { bsonType: "string" } }
            }
        }
    }
});

db.createCollection("conversations", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["participants", "conversation_type"],
            properties: {
                participants: { 
                    bsonType: "array", 
                    items: { bsonType: "string" },
                    minItems: 2
                },
                conversation_type: { enum: ["private", "group"] },
                title: { bsonType: "string", maxLength: 100 },
                created_at: { bsonType: "date" },
                last_message_at: { bsonType: "date" },
                quantum_encrypted: { bsonType: "bool" }
            }
        }
    }
});

db.createCollection("chat_messages", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["conversation_id", "sender_id", "message_type", "content"],
            properties: {
                conversation_id: { bsonType: "string" },
                sender_id: { bsonType: "string" },
                receiver_id: { bsonType: "string" },
                message_type: { enum: ["text", "image", "capsule_share", "quantum_state"] },
                content: { bsonType: "object" },
                timestamp: { bsonType: "date" },
                status: { enum: ["sent", "delivered", "read"] },
                reply_to: { bsonType: "string" }
            }
        }
    }
});

db.createCollection("friendships", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["requester_id", "addressee_id", "status"],
            properties: {
                requester_id: { bsonType: "string" },
                addressee_id: { bsonType: "string" },
                status: { enum: ["pending", "accepted", "blocked"] },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

db.createCollection("capsule_permissions", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["capsule_id", "owner_id", "shared_with_user_id", "permission_level"],
            properties: {
                capsule_id: { bsonType: "string" },
                owner_id: { bsonType: "string" },
                shared_with_user_id: { bsonType: "string" },
                permission_level: { enum: ["view", "comment", "interact"] },
                granted_at: { bsonType: "date" },
                expires_at: { bsonType: "date" },
                is_active: { bsonType: "bool" }
            }
        }
    }
});

// Create remaining collections
const remainingCollections = [
    "quantum_circuits", "quantum_measurements", "quantum_connections",
    "quantum_messages", "quantum_images", "user_sessions", "quantum_experiments",
    "system_notifications", "quantum_vault_items", "activity_logs",
    "quantum_states", "configuration_settings"
];

remainingCollections.forEach(collection => {
    db.createCollection(collection);
    print(`Created collection: ${collection}`);
});

// Create comprehensive indexes
const indexes = [
    // User indexes
    { collection: "users", index: { "email": 1 }, options: { unique: true } },
    { collection: "users", index: { "username": 1 }, options: { unique: true } },
    
    // Capsule indexes
    { collection: "temporal_capsules", index: { "user_id": 1, "created_at": -1 } },
    { collection: "temporal_capsules", index: { "unlock_date": 1 } },
    { collection: "temporal_capsules", index: { "status": 1 } },
    { collection: "temporal_capsules", index: { "tags": 1 } },
    
    // Chat indexes
    { collection: "conversations", index: { "participants": 1 } },
    { collection: "conversations", index: { "last_message_at": -1 } },
    { collection: "chat_messages", index: { "conversation_id": 1, "timestamp": -1 } },
    { collection: "chat_messages", index: { "sender_id": 1, "timestamp": -1 } },
    { collection: "chat_messages", index: { "status": 1 } },
    
    // Friendship indexes
    { collection: "friendships", index: { "requester_id": 1, "status": 1 } },
    { collection: "friendships", index: { "addressee_id": 1, "status": 1 } },
    { collection: "friendships", index: { "requester_id": 1, "addressee_id": 1 }, options: { unique: true } },
    
    // Permission indexes
    { collection: "capsule_permissions", index: { "capsule_id": 1 } },
    { collection: "capsule_permissions", index: { "shared_with_user_id": 1, "is_active": 1 } },
    { collection: "capsule_permissions", index: { "owner_id": 1 } },
    { collection: "capsule_permissions", index: { "expires_at": 1 } },
    
    // Quantum indexes
    { collection: "quantum_circuits", index: { "user_id": 1, "created_at": -1 } },
    { collection: "quantum_measurements", index: { "circuit_id": 1, "timestamp": -1 } },
    { collection: "quantum_vault_items", index: { "user_id": 1, "item_type": 1 } },
    { collection: "activity_logs", index: { "user_id": 1, "timestamp": -1 } }
];

indexes.forEach(indexSpec => {
    db[indexSpec.collection].createIndex(indexSpec.index, indexSpec.options || {});
    print(`Created index on ${indexSpec.collection}: ${JSON.stringify(indexSpec.index)}`);
});

// Insert sample data for development
const sampleUser = {
    username: "quantum_admin",
    email: "admin@quantumdashboard.com",
    hashed_password: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.w8ksbYGLa", // password123
    full_name: "Quantum Administrator",
    quantum_level: 10,
    is_active: true,
    created_at: new Date(),
    total_capsules: 0,
    unlocked_capsules: 0,
    quantum_connections: []
};

db.users.insertOne(sampleUser);
print("Inserted sample admin user");

// Create sample temporal capsule
const adminId = db.users.findOne({username: "quantum_admin"})._id.toString();

const sampleCapsule = {
    user_id: adminId,
    title: "Welcome to Quantum Dashboard",
    description: "Your first quantum temporal capsule",
    capsule_type: "message",
    content: {
        message: "Welcome to the future of temporal storage!",
        quantum_signature: "∞"
    },
    unlock_date: new Date(Date.now() - 24*60*60*1000), // Unlocked (yesterday)
    created_at: new Date(),
    status: "unlocked",
    access_count: 0,
    tags: ["welcome", "tutorial"]
};

db.temporal_capsules.insertOne(sampleCapsule);
print("Inserted sample capsule");

print("Enhanced MongoDB initialization completed successfully!");
print("Collections created: " + collections.length);
print("Indexes created: " + indexes.length);
