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

ax::Node* UIJsonBuilder::buildLayer(const rapidjson::Value& layerData, const rapidjson::Value& theme, const rapidjson::Value& state) {
    if (!layerData.HasMember("shape") || !layerData["shape"].IsString()) {
        return nullptr;
    }
    
    std::string shape = layerData["shape"].GetString();
    
    ax::Color3B fillColor = ax::Color3B::WHITE;
    if (layerData.HasMember("style") && layerData["style"].HasMember("fill") && layerData["style"]["fill"].IsString()) {
        fillColor = parseColor(layerData["style"]["fill"].GetString(), theme["colors"]);
    }
    
    ax::Node* node = nullptr;
    
    if (shape == "roundedRect") {
        float w = layerData["rect"]["width"].GetFloat();
        float h = layerData["rect"]["height"].GetFloat();
        auto layerColor = ax::LayerColor::create(ax::Color4B(fillColor.r, fillColor.g, fillColor.b, 255), w, h);
        layerColor->setIgnoreAnchorPointForPosition(false);
        layerColor->setAnchorPoint(ax::Vec2(0, 1)); // Top-left anchor for rects by default
        node = layerColor;
    } else if (shape == "text") {
        std::string textValue = layerData["text"]["value"].GetString();
        std::string boundValue = resolveBindValue(layerData, state);
        if (!boundValue.empty()) {
            textValue = boundValue;
        }
        float fontSize = layerData["text"]["size"].GetFloat();
        
        // For now, use system font
        auto label = ax::Label::createWithSystemFont(textValue, "Arial", fontSize);
        label->setColor(fillColor);
        label->setAnchorPoint(ax::Vec2(0, 1)); // Top-left anchor for text
        node = label;
    }
    
    if (node && layerData.HasMember("rect")) {
        float x = layerData["rect"]["x"].GetFloat();
        float y = layerData["rect"]["y"].GetFloat();
        // Offset from component's top-left origin. Since Cocos Y is up, and SVG Y is down,
        // we use a negative Y offset from the top.
        node->setPosition(ax::Vec2(x, -y));
    }
    
    return node;
}

ax::Node* UIJsonBuilder::buildComponent(const rapidjson::Value& componentData, const rapidjson::Value& theme, const rapidjson::Value& state) {
    auto compNode = ax::Node::create();
    
    if (componentData.HasMember("layers") && componentData["layers"].IsArray()) {
        const auto& layers = componentData["layers"];
        for (rapidjson::SizeType i = 0; i < layers.Size(); i++) {
            auto layerNode = buildLayer(layers[i], theme, state);
            if (layerNode) {
                compNode->addChild(layerNode);
            }
        }
    }
    return compNode;
}

ax::Node* UIJsonBuilder::buildFromFile(const std::string& filepath) {
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
            auto compNode = buildComponent(*componentMap[compId], theme, state);
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
