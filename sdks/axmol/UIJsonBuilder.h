#pragma once

#include "axmol.h"
#include "ui/CocosGUI.h"
#include "rapidjson/document.h"
#include <string>
#include <unordered_map>
#include <functional>

typedef std::function<void(ax::Node* node, const rapidjson::Value& layerData)> NodeCreatedCallback;

class UIJsonBuilder {
public:
    static UIJsonBuilder* getInstance();
    
    // JSONファイルからUIノード（レイアウトのルート）を生成して返す
    ax::Node* buildFromFile(const std::string& filepath, NodeCreatedCallback callback = nullptr);

private:
    UIJsonBuilder() = default;
    ~UIJsonBuilder() = default;

    ax::Color3B parseColor(const std::string& colorStr, const rapidjson::Value& themeColors);
    std::string resolveBindValue(const rapidjson::Value& layerData, const rapidjson::Value& state);
    
    ax::Node* buildInstance(
        const rapidjson::Value& inst, 
        const std::unordered_map<std::string, const rapidjson::Value*>& componentMap,
        const rapidjson::Value& theme, 
        const rapidjson::Value& state, 
        NodeCreatedCallback callback
    );

    ax::Node* buildComponentVisuals(
        const rapidjson::Value& componentData, 
        const rapidjson::Value& inst,
        const rapidjson::Value& theme, 
        const rapidjson::Value& state, 
        NodeCreatedCallback callback
    );
    
    ax::Node* buildLayer(
        const rapidjson::Value& layerData, 
        const rapidjson::Value& inst,
        const rapidjson::Value& theme, 
        const rapidjson::Value& state, 
        NodeCreatedCallback callback
    );
};
