#pragma once

#include "axmol.h"
#include "ui/CocosGUI.h"
#include "rapidjson/document.h"
#include <string>
#include <unordered_map>

class UIJsonBuilder {
public:
    static UIJsonBuilder* getInstance();
    
    // JSONファイルからUIノード（レイアウトのルート）を生成して返す
    ax::Node* buildFromFile(const std::string& filepath);

private:
    UIJsonBuilder() = default;
    ~UIJsonBuilder() = default;

    ax::Color3B parseColor(const std::string& colorStr, const rapidjson::Value& themeColors);
    std::string resolveBindValue(const rapidjson::Value& layerData, const rapidjson::Value& state);
    ax::Node* buildComponent(const rapidjson::Value& componentData, const rapidjson::Value& theme, const rapidjson::Value& state);
    ax::Node* buildLayer(const rapidjson::Value& layerData, const rapidjson::Value& theme, const rapidjson::Value& state);
};
