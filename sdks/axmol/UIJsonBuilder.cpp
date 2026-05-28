#include "UIJsonBuilder.h"
#include <fstream>

using namespace ax;

UIJsonBuilder* UIJsonBuilder::getInstance() {
    static UIJsonBuilder instance;
    return &instance;
}

ax::Color3B UIJsonBuilder::parseColor(const std::string& colorStr, const rapidjson::Value& themeColors) {
    std::string hexStr = colorStr;
    // Check if it's a theme variable like "theme.colors.textPrimary"
    if (colorStr.find("theme.colors.") == 0) {
        std::string key = colorStr.substr(13);
        if (themeColors.HasMember(key.c_str()) && themeColors[key.c_str()].IsString()) {
            hexStr = themeColors[key.c_str()].GetString();
        }
    }
    
    if (hexStr.length() > 0 && hexStr[0] == '#') {
        hexStr = hexStr.substr(1);
    }
    
    if (hexStr.length() == 6) {
        int r, g, b;
        sscanf(hexStr.c_str(), "%02x%02x%02x", &r, &g, &b);
        return ax::Color3B(r, g, b);
    }
    return ax::Color3B::WHITE;
}

std::string UIJsonBuilder::resolveBindValue(const rapidjson::Value& layerData, const rapidjson::Value& state) {
    if (!layerData.HasMember("bind") || !layerData["bind"].IsObject()) return "";
    const auto& bind = layerData["bind"];
    if (!bind.HasMember("value") || !bind["value"].IsObject()) return "";
    const auto& valBind = bind["value"];
    if (!valBind.HasMember("var") || !valBind["var"].IsString()) return "";
    
    std::string varPath = valBind["var"].GetString();
    
    // Split varPath by '.' and traverse state
    size_t start = 0;
    size_t end = varPath.find('.');
    const rapidjson::Value* current = &state;
    
    while (end != std::string::npos) {
        std::string segment = varPath.substr(start, end - start);
        if (!current->IsObject() || !current->HasMember(segment.c_str())) return "";
        current = &(*current)[segment.c_str()];
        start = end + 1;
        end = varPath.find('.', start);
    }
    
    std::string lastSegment = varPath.substr(start);
    if (!current->IsObject() || !current->HasMember(lastSegment.c_str())) return "";
    
    const rapidjson::Value& finalVal = (*current)[lastSegment.c_str()];
    if (finalVal.IsString()) return finalVal.GetString();
    if (finalVal.IsInt()) return std::to_string(finalVal.GetInt());
    if (finalVal.IsFloat()) return std::to_string(finalVal.GetFloat());
    
    return "";
}

ax::Node* UIJsonBuilder::buildLayer(const rapidjson::Value& layerData, const rapidjson::Value& theme, const rapidjson::Value& state, NodeCreatedCallback callback) {
    std::string typeStr = layerData.HasMember("type") && layerData["type"].IsString() ? layerData["type"].GetString() : "";
    std::string shape = layerData.HasMember("shape") && layerData["shape"].IsString() ? layerData["shape"].GetString() : "";
    
    ax::Color3B fillColor = ax::Color3B::WHITE;
    if (layerData.HasMember("style") && layerData["style"].HasMember("fill") && layerData["style"]["fill"].IsString()) {
        fillColor = parseColor(layerData["style"]["fill"].GetString(), theme["colors"]);
    }
    
    ax::Node* node = nullptr;
    
    if (typeStr == "image") {
        if (layerData.HasMember("texture") && layerData["texture"].IsString()) {
            std::string texPath = layerData["texture"].GetString();
            auto sprite = ax::Sprite::create(texPath);
            if (sprite) {
                sprite->setAnchorPoint(ax::Vec2(0, 1)); // Top-left anchor
                node = sprite;
            } else {
                AXLOG("Failed to load texture: %s", texPath.c_str());
            }
        }
    } else if (shape == "roundedRect") {
        float w = layerData["rect"]["width"].GetFloat();
        float h = layerData["rect"]["height"].GetFloat();
        
        GLubyte opacity = 255;
        if (layerData.HasMember("fillOpacity") && layerData["fillOpacity"].IsInt()) {
            opacity = static_cast<GLubyte>(layerData["fillOpacity"].GetInt());
        }
        
        auto layerColor = ax::LayerColor::create(ax::Color4B(fillColor.r, fillColor.g, fillColor.b, opacity), w, h);
        layerColor->setIgnoreAnchorPointForPosition(false);
        layerColor->setAnchorPoint(ax::Vec2(0, 1)); // Top-left anchor for rects by default
        node = layerColor;
    } else if (shape == "text" || typeStr == "text") {
        std::string textValue = "";
        if (layerData.HasMember("text") && layerData["text"].IsObject() && layerData["text"].HasMember("value")) {
            textValue = layerData["text"]["value"].GetString();
        } else if (layerData.HasMember("text") && layerData["text"].IsString()) {
            textValue = layerData["text"].GetString();
        }
        
        std::string boundValue = resolveBindValue(layerData, state);
        if (!boundValue.empty()) {
            textValue = boundValue;
        }
        
        float fontSize = 24.0f;
        if (layerData.HasMember("text") && layerData["text"].IsObject() && layerData["text"].HasMember("size")) {
            fontSize = layerData["text"]["size"].GetFloat();
        } else if (layerData.HasMember("fontSize") && layerData["fontSize"].IsNumber()) {
            fontSize = layerData["fontSize"].GetFloat();
        }
        
        if (layerData.HasMember("color") && layerData["color"].IsString()) {
            fillColor = parseColor(layerData["color"].GetString(), theme["colors"]);
        }
        
        // For now, use system font
        auto label = ax::Label::createWithSystemFont(textValue, "Arial", fontSize);
        label->setColor(fillColor);
        label->setAnchorPoint(ax::Vec2(0, 1)); // Top-left anchor for text
        node = label;
    }
    
    if (node) {
        if (layerData.HasMember("name") && layerData["name"].IsString()) {
            node->setName(layerData["name"].GetString());
        }
        
        float x = 0;
        float y = 0;
        if (layerData.HasMember("rect")) {
            x = layerData["rect"]["x"].GetFloat();
            y = layerData["rect"]["y"].GetFloat();
        } else if (layerData.HasMember("position")) {
            x = layerData["position"]["x"].GetFloat();
            y = layerData["position"]["y"].GetFloat();
        }
        // Offset from component's top-left origin. Since Cocos Y is up, and SVG Y is down,
        // we use a negative Y offset from the top.
        node->setPosition(ax::Vec2(x, -y));
        
        if (layerData.HasMember("scale")) {
            if (layerData["scale"].IsNumber()) {
                node->setScale(layerData["scale"].GetFloat());
            } else if (layerData["scale"].IsObject()) {
                float sx = layerData["scale"].HasMember("x") ? layerData["scale"]["x"].GetFloat() : 1.0f;
                float sy = layerData["scale"].HasMember("y") ? layerData["scale"]["y"].GetFloat() : 1.0f;
                node->setScaleX(sx);
                node->setScaleY(sy);
            }
        }
        if (layerData.HasMember("opacity") && layerData["opacity"].IsInt()) {
            node->setOpacity(static_cast<GLubyte>(layerData["opacity"].GetInt()));
        }
        
        // --- Standard UI Animations parsing (Handled by SDK) ---
        if (layerData.HasMember("animation") && layerData["animation"].IsObject()) {
            const auto& animData = layerData["animation"];
            if (animData.HasMember("loop") && animData["loop"].IsString()) {
                std::string loopType = animData["loop"].GetString();
                if (loopType == "bounce") {
                    auto moveUp = ax::MoveBy::create(0.5f, ax::Vec2(0, 10));
                    auto moveDown = moveUp->reverse();
                    auto seq = ax::Sequence::create(moveUp, moveDown, nullptr);
                    node->runAction(ax::RepeatForever::create(seq));
                }
            }
            if (animData.HasMember("enter") && animData["enter"].IsString()) {
                std::string enterType = animData["enter"].GetString();
                if (enterType == "fade_slide_up") {
                    node->setOpacity(0);
                    node->setPositionY(node->getPositionY() - 20); // start 20px lower
                    auto fadeIn = ax::FadeIn::create(0.4f);
                    auto slideUp = ax::MoveBy::create(0.4f, ax::Vec2(0, 20));
                    node->runAction(ax::Spawn::createWithTwoActions(fadeIn, slideUp));
                }
            }
        }
        
        // --- Invoke Callback for Custom Game Logic ---
        if (callback) {
            callback(node, layerData);
        }
    }
    
    return node;
}

ax::Node* UIJsonBuilder::buildComponent(const rapidjson::Value& componentData, const rapidjson::Value& theme, const rapidjson::Value& state, NodeCreatedCallback callback) {
    auto compNode = ax::Node::create();
    
    if (componentData.HasMember("layers") && componentData["layers"].IsArray()) {
        const auto& layers = componentData["layers"];
        for (rapidjson::SizeType i = 0; i < layers.Size(); i++) {
            auto layerNode = buildLayer(layers[i], theme, state, callback);
            if (layerNode) {
                compNode->addChild(layerNode);
            }
        }
    }
    return compNode;
}

ax::Node* UIJsonBuilder::buildFromFile(const std::string& filepath, NodeCreatedCallback callback) {
    std::string fullPath = FileUtils::getInstance()->fullPathForFilename(filepath);
    std::string content = FileUtils::getInstance()->getStringFromFile(fullPath);
    
    if (content.empty()) {
        AXLOG("Failed to load JSON file or file is empty: %s", fullPath.c_str());
        return nullptr;
    }

    rapidjson::Document doc;
    doc.Parse(content.c_str());
    
    if (doc.HasParseError() || !doc.IsObject()) {
        AXLOG("Failed to parse UI JSON: %s", filepath.c_str());
        return nullptr;
    }
    
    if (!doc.HasMember("assetType") || std::string(doc["assetType"].GetString()) != "screen") {
        AXLOG("Invalid assetType for UI JSON: %s", filepath.c_str());
        return nullptr;
    }
    
    const auto& theme = doc["theme"];
    const auto& components = doc["components"];
    const auto& instances = doc["instances"];
    
    // Extract mockState if it exists
    rapidjson::Value emptyState(rapidjson::kObjectType);
    const rapidjson::Value& state = doc.HasMember("mockState") ? doc["mockState"] : emptyState;
    
    auto rootNode = ax::Node::create();
    // Default canvas size
    float canvasWidth = 720;
    float canvasHeight = 1280;
    
    if (doc.HasMember("canvas")) {
        canvasWidth = doc["canvas"]["width"].GetFloat();
        canvasHeight = doc["canvas"]["height"].GetFloat();
    }
    rootNode->setContentSize(ax::Size(canvasWidth, canvasHeight));
    
    // Map components by id for quick lookup
    std::unordered_map<std::string, const rapidjson::Value*> componentMap;
    for (rapidjson::SizeType i = 0; i < components.Size(); i++) {
        std::string compId = components[i]["id"].GetString();
        componentMap[compId] = &components[i];
    }
    
    for (rapidjson::SizeType i = 0; i < instances.Size(); i++) {
        const auto& inst = instances[i];
        std::string compId = inst["componentId"].GetString();
        
        if (componentMap.find(compId) != componentMap.end()) {
            auto compNode = buildComponent(*componentMap[compId], theme, state, callback);
            if (compNode) {
                float w = inst["size"]["width"].GetFloat();
                float h = inst["size"]["height"].GetFloat();
                compNode->setContentSize(ax::Size(w, h));
                
                float x = inst["offset"]["x"].GetFloat();
                float y = inst["offset"]["y"].GetFloat();
                
                // SVG coordinates to Cocos coordinates mapping
                // SVG origin is Top-Left (Y goes down)
                // Cocos origin is Bottom-Left (Y goes up)
                // We'll place the rootNode at (0,0) with its own anchor (0,0).
                // The components need to be placed such that top of canvas maps to Y = canvasHeight
                
                compNode->setAnchorPoint(ax::Vec2(0, 1)); // Anchor at top-left
                compNode->setPosition(ax::Vec2(x, canvasHeight - y));
                
                rootNode->addChild(compNode);
            }
        }
    }
    
    return rootNode;
}
