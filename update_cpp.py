import os

cpp_code = """#include "UIJsonBuilder.h"
#include <fstream>
#include <algorithm>

using namespace ax;

UIJsonBuilder* UIJsonBuilder::getInstance() {
    static UIJsonBuilder instance;
    return &instance;
}

ax::Color3B UIJsonBuilder::parseColor(const std::string& colorStr, const rapidjson::Value& themeColors) {
    std::string hexStr = colorStr;
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
    } else if (hexStr.length() == 8) { // RRGGBBAA or AARRGGBB, assuming RRGGBB for Color3B
        int r, g, b, a;
        sscanf(hexStr.c_str(), "%02x%02x%02x%02x", &r, &g, &b, &a);
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

ax::Node* UIJsonBuilder::buildLayer(const rapidjson::Value& layerData, const rapidjson::Value& inst, const rapidjson::Value& theme, const rapidjson::Value& state, NodeCreatedCallback callback) {
    std::string typeStr = layerData.HasMember("type") && layerData["type"].IsString() ? layerData["type"].GetString() : "";
    std::string shape = layerData.HasMember("shape") && layerData["shape"].IsString() ? layerData["shape"].GetString() : "";
    
    ax::Color3B fillColor = ax::Color3B::WHITE;
    if (layerData.HasMember("style") && layerData["style"].HasMember("fill") && layerData["style"]["fill"].IsString()) {
        fillColor = parseColor(layerData["style"]["fill"].GetString(), theme["colors"]);
    }
    // Overrides from inst
    if (inst.HasMember("props") && inst["props"].HasMember("fillColor") && inst["props"]["fillColor"].IsString()) {
        std::string overrideColor = inst["props"]["fillColor"].GetString();
        if (overrideColor != "transparent") {
            fillColor = parseColor(overrideColor, theme["colors"]);
        }
    } else if (inst.HasMember("overrideFill") && inst["overrideFill"].IsString()) {
        fillColor = parseColor(inst["overrideFill"].GetString(), theme["colors"]);
    }
    
    ax::Node* node = nullptr;
    
    if (typeStr == "image") {
        std::string texPath = "";
        if (inst.HasMember("props") && inst["props"].HasMember("imageNormal") && inst["props"]["imageNormal"].IsString()) {
            texPath = inst["props"]["imageNormal"].GetString();
        } else if (inst.HasMember("props") && inst["props"].HasMember("imagePath") && inst["props"]["imagePath"].IsString()) {
            texPath = inst["props"]["imagePath"].GetString();
        } else if (inst.HasMember("imagePath") && inst["imagePath"].IsString()) {
            texPath = inst["imagePath"].GetString();
        } else if (inst.HasMember("imageNormal") && inst["imageNormal"].IsString()) {
            texPath = inst["imageNormal"].GetString();
        } else if (layerData.HasMember("texture") && layerData["texture"].IsString()) {
            texPath = layerData["texture"].GetString();
        }
        
        if (!texPath.empty()) {
            auto sprite = ax::Sprite::create(texPath);
            if (sprite) {
                sprite->setAnchorPoint(ax::Vec2(0, 1)); // Top-left anchor
                node = sprite;
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
        layerColor->setAnchorPoint(ax::Vec2(0, 1));
        node = layerColor;
    } else if (shape == "text" || typeStr == "text") {
        std::string textValue = "";
        if (layerData.HasMember("text") && layerData["text"].IsObject() && layerData["text"].HasMember("value")) {
            textValue = layerData["text"]["value"].GetString();
        } else if (layerData.HasMember("text") && layerData["text"].IsString()) {
            textValue = layerData["text"].GetString();
        }
        
        if (inst.HasMember("props") && inst["props"].HasMember("text") && inst["props"]["text"].IsString()) {
            textValue = inst["props"]["text"].GetString();
        } else if (inst.HasMember("overrideText") && inst["overrideText"].IsString()) {
            textValue = inst["overrideText"].GetString();
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
        
        auto label = ax::Label::createWithSystemFont(textValue, "Arial", fontSize);
        label->setColor(fillColor);
        label->setAnchorPoint(ax::Vec2(0, 1));
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
    }
    
    return node;
}

ax::Node* UIJsonBuilder::buildComponentVisuals(const rapidjson::Value& componentData, const rapidjson::Value& inst, const rapidjson::Value& theme, const rapidjson::Value& state, NodeCreatedCallback callback) {
    auto compNode = ax::Node::create();
    compNode->setAnchorPoint(ax::Vec2(0, 1)); // Top left origin
    
    if (componentData.HasMember("layers") && componentData["layers"].IsArray()) {
        const auto& layers = componentData["layers"];
        for (rapidjson::SizeType i = 0; i < layers.Size(); i++) {
            auto layerNode = buildLayer(layers[i], inst, theme, state, callback);
            if (layerNode) {
                compNode->addChild(layerNode);
            }
        }
    }
    
    return compNode;
}

ax::Node* UIJsonBuilder::buildInstance(
    const rapidjson::Value& inst, 
    const std::unordered_map<std::string, const rapidjson::Value*>& componentMap,
    const rapidjson::Value& theme, 
    const rapidjson::Value& state, 
    NodeCreatedCallback callback
) {
    if (!inst.HasMember("componentId")) return nullptr;
    std::string compId = inst["componentId"].GetString();
    
    if (componentMap.find(compId) == componentMap.end()) return nullptr;
    const rapidjson::Value* compData = componentMap.at(compId);
    
    auto node = buildComponentVisuals(*compData, inst, theme, state, callback);
    if (!node) return nullptr;
    
    float nodeW = 0, nodeH = 0;
    if (inst.HasMember("size")) {
        nodeW = inst["size"]["width"].GetFloat();
        nodeH = inst["size"]["height"].GetFloat();
        node->setContentSize(ax::Size(nodeW, nodeH));
    }
    
    // Container Logic for Children
    if (inst.HasMember("children") && inst["children"].IsArray()) {
        const auto& children = inst["children"];
        std::string visualType = compData->HasMember("visualType") && (*compData)["visualType"].IsString() ? (*compData)["visualType"].GetString() : "";
        
        float spacingX = 8.0f;
        float spacingY = 8.0f;
        bool staggerChildren = false;
        if (inst.HasMember("props") && inst["props"].IsObject()) {
            if (inst["props"].HasMember("spacingX")) spacingX = inst["props"]["spacingX"].GetFloat();
            if (inst["props"].HasMember("spacingY")) spacingY = inst["props"]["spacingY"].GetFloat();
            if (inst["props"].HasMember("staggerChildren")) staggerChildren = inst["props"]["staggerChildren"].GetBool();
        }
        
        float currentX = 0;
        float currentY = 0; // Relative to top-left, going down is negative in Cocos
        
        for (rapidjson::SizeType i = 0; i < children.Size(); i++) {
            auto childNode = buildInstance(children[i], componentMap, theme, state, callback);
            if (childNode) {
                // Layout logic
                if (visualType == "vbox") {
                    childNode->setPosition(ax::Vec2(0, currentY));
                    currentY -= (childNode->getContentSize().height + spacingY);
                } else if (visualType == "hbox") {
                    childNode->setPosition(ax::Vec2(currentX, 0));
                    currentX += (childNode->getContentSize().width + spacingX);
                } else if (visualType == "grid") {
                    int columns = 3;
                    if (inst.HasMember("props") && inst["props"].HasMember("columns")) columns = inst["props"]["columns"].GetInt();
                    if (columns < 1) columns = 1;
                    int col = i % columns;
                    int row = i / columns;
                    float cx = col * (childNode->getContentSize().width + spacingX);
                    float cy = row * (childNode->getContentSize().height + spacingY);
                    childNode->setPosition(ax::Vec2(cx, -cy));
                } else {
                    // Default absolute positioning from export
                    if (children[i].HasMember("offset")) {
                        float cx = children[i]["offset"]["x"].GetFloat();
                        float cy = children[i]["offset"]["y"].GetFloat();
                        // Relative to parent, which also has top-left anchor in our setup
                        childNode->setPosition(ax::Vec2(cx, -cy));
                    }
                }
                
                // Stagger Animation logic
                if (staggerChildren) {
                    float delay = i * 0.1f;
                    childNode->setOpacity(0);
                    // Add a slide-up stagger effect
                    childNode->setPositionY(childNode->getPositionY() - 20);
                    auto delayAction = ax::DelayTime::create(delay);
                    auto fadeIn = ax::FadeIn::create(0.3f);
                    auto moveUp = ax::MoveBy::create(0.3f, ax::Vec2(0, 20));
                    auto spawn = ax::Spawn::createWithTwoActions(fadeIn, moveUp);
                    auto seq = ax::Sequence::create(delayAction, spawn, nullptr);
                    childNode->runAction(seq);
                }
                
                node->addChild(childNode);
            }
        }
    }
    
    // Self Animation logic
    std::string animType = "";
    if (inst.HasMember("props") && inst["props"].HasMember("animation") && inst["props"]["animation"].IsString()) {
        animType = inst["props"]["animation"].GetString();
    }
    
    if (!animType.empty() && animType != "none") {
        if (animType == "blink") {
            auto fadeOut = ax::FadeOut::create(0.5f);
            auto fadeIn = ax::FadeIn::create(0.5f);
            node->runAction(ax::RepeatForever::create(ax::Sequence::create(fadeOut, fadeIn, nullptr)));
        } else if (animType == "pulse") {
            auto scaleUp = ax::ScaleTo::create(0.5f, 1.05f);
            auto scaleDown = ax::ScaleTo::create(0.5f, 1.0f);
            node->runAction(ax::RepeatForever::create(ax::Sequence::create(scaleUp, scaleDown, nullptr)));
        } else if (animType == "pop-in") {
            node->setScale(0.0f);
            auto scaleTo = ax::ScaleTo::create(0.3f, 1.0f);
            auto ease = ax::EaseBackOut::create(scaleTo);
            node->runAction(ease);
        } else if (animType == "slide-up") {
            node->setOpacity(0);
            node->setPositionY(node->getPositionY() - 30);
            node->runAction(ax::Spawn::createWithTwoActions(ax::FadeIn::create(0.3f), ax::MoveBy::create(0.3f, ax::Vec2(0, 30))));
        } else if (animType == "slide-down") {
            node->setOpacity(0);
            node->setPositionY(node->getPositionY() + 30);
            node->runAction(ax::Spawn::createWithTwoActions(ax::FadeIn::create(0.3f), ax::MoveBy::create(0.3f, ax::Vec2(0, -30))));
        } else if (animType == "slide-in-left") {
            node->setOpacity(0);
            node->setPositionX(node->getPositionX() - 50);
            node->runAction(ax::Spawn::createWithTwoActions(ax::FadeIn::create(0.3f), ax::MoveBy::create(0.3f, ax::Vec2(50, 0))));
        } else if (animType == "slide-in-right") {
            node->setOpacity(0);
            node->setPositionX(node->getPositionX() + 50);
            node->runAction(ax::Spawn::createWithTwoActions(ax::FadeIn::create(0.3f), ax::MoveBy::create(0.3f, ax::Vec2(-50, 0))));
        } else if (animType == "fade-in") {
            node->setOpacity(0);
            node->runAction(ax::FadeIn::create(0.4f));
        } else if (animType == "shake") {
            auto move1 = ax::MoveBy::create(0.05f, ax::Vec2(5, 0));
            auto move2 = ax::MoveBy::create(0.05f, ax::Vec2(-10, 0));
            auto move3 = ax::MoveBy::create(0.05f, ax::Vec2(5, 0));
            auto seq = ax::Sequence::create(move1, move2, move3, nullptr);
            node->runAction(ax::RepeatForever::create(ax::Sequence::create(seq, ax::DelayTime::create(2.0f), nullptr)));
        } else if (animType == "shiny") {
            auto shine = ax::LayerColor::create(ax::Color4B(255, 255, 255, 100), nodeW / 2, nodeH);
            shine->setAnchorPoint(ax::Vec2(0, 1));
            shine->setPosition(ax::Vec2(-nodeW, 0));
            shine->setSkewX(-20.0f);
            
            auto move = ax::MoveBy::create(1.0f, ax::Vec2(nodeW * 2, 0));
            auto reset = ax::Place::create(ax::Vec2(-nodeW, 0));
            auto seq = ax::Sequence::create(move, ax::DelayTime::create(1.5f), reset, nullptr);
            
            auto clip = ax::ClippingNode::create();
            auto stencil = ax::LayerColor::create(ax::Color4B(255, 255, 255, 255), nodeW, nodeH);
            stencil->setAnchorPoint(ax::Vec2(0, 1));
            stencil->setPosition(ax::Vec2(0, 0));
            clip->setStencil(stencil);
            clip->addChild(shine);
            
            node->addChild(clip);
            shine->runAction(ax::RepeatForever::create(seq));
        }
    }
    
    if (callback) {
        callback(node, inst);
    }
    
    return node;
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
    
    rapidjson::Value emptyState(rapidjson::kObjectType);
    const rapidjson::Value& state = doc.HasMember("mockState") ? doc["mockState"] : emptyState;
    
    auto rootNode = ax::Node::create();
    
    float canvasWidth = 720;
    float canvasHeight = 1280;
    
    if (doc.HasMember("canvas")) {
        canvasWidth = doc["canvas"]["width"].GetFloat();
        canvasHeight = doc["canvas"]["height"].GetFloat();
    }
    rootNode->setContentSize(ax::Size(canvasWidth, canvasHeight));
    
    std::unordered_map<std::string, const rapidjson::Value*> componentMap;
    for (rapidjson::SizeType i = 0; i < components.Size(); i++) {
        std::string compId = components[i]["id"].GetString();
        componentMap[compId] = &components[i];
    }
    
    for (rapidjson::SizeType i = 0; i < instances.Size(); i++) {
        auto instNode = buildInstance(instances[i], componentMap, theme, state, callback);
        if (instNode) {
            float x = 0, y = 0;
            if (instances[i].HasMember("offset")) {
                x = instances[i]["offset"]["x"].GetFloat();
                y = instances[i]["offset"]["y"].GetFloat();
            }
            instNode->setAnchorPoint(ax::Vec2(0, 1));
            instNode->setPosition(ax::Vec2(x, canvasHeight - y));
            rootNode->addChild(instNode);
        }
    }
    
    return rootNode;
}
"""
with open("sdks/axmol/UIJsonBuilder.cpp", "w") as f:
    f.write(cpp_code)
