export default () => {
   return {
      enableSceneReloading: true,
      scenes: [
            { name: "example1"  , path: "./example1.js"  , public: false },
            { name: "example2"  , path: "./example2.js"  , public: false },
            { name: "example3"  , path: "./example3.js"  , public: false },
            { name: "example4"  , path: "./example4.js"  , public: false },
            { name: "example5"  , path: "./example5.js"  , public: false },
            { name: "example6"  , path: "./example6.js"  , public: false },
            { name: "example7"  , path: "./example7.js"  , public: false },
            { name: "example8"  , path: "./example8.js"  , public: false },

            { name: "simple"    , path: "./simple.js"    , public: false },
            { name: "pinscreen" , path: "./pinscreen.js" , public: false },
            { name: "opacity"   , path: "./opacity.js"   , public: false },
            { name: "intersect" , path: "./intersect.js" , public: false },
            { name: "shaders"   , path: "./shaders.js"   , public: false },
            { name: "raytrace"  , path: "./raytrace.js"  , public: false },
            { name: "particles" , path: "./particles.js" , public: false },

            { name: "controllerBeam" , path: "./controllerBeam.js" , public: false },
            { name: "diagram1"       , path: "./diagram1.js"       , public: false },
            { name: "clock"          , path: "./clock.js"          , public: false },
            { name: "particleNoise"  , path: "./particleNoise.js"  , public: false },

            { name: "hud"           , path: "./hud.js"           , public: false },
            { name: "g2Example1"    , path: "./g2Example1.js"    , public: false },
            { name: "intersect2"    , path: "./intersect2.js"    , public: false },
            { name: "large_texture" , path: "./large_texture.js" , public: false },
            { name: "combineMeshes" , path: "./combineMeshes.js" , public: false },
            { name: "widgets"       , path: "./widgets.js"       , public: false },
            { name: "statue"        , path: "./statue.js"        , public: false },
            { name: "severalGLTF"   , path: "./severalGLTF.js"   , public: false },

            { name: "wordcloud"     , path: "./wordcloud.js"     , public: false },
            { name: "wordcloud2"    , path: "./wordcloud2.js"    , public: false },
            { name: "wordcloud3"    , path: "./wordcloud3.js"    , public: false },
            { name: "wordcloud4"    , path: "./wordcloud4.js"    , public: false },
            { name: "wordcloud5"    , path: "./wordcloud5.js"    , public: false },
            { name: "wordcloud6"    , path: "./wordcloud6.js"    , public: false },
            { name: "wordcloud7"    , path: "./wordcloud7.js"    , public: false },

            { name: "screen"         , path: "./screen.js"            , public: true },
            { name: "stock"          , path: "./stock.js"             , public: true },
            { name: "aiQuery-console", path: "./demoAIQueryConsole.js", public: true },
            { name: "aiQuery"        , path: "./demoAIQuery.js"       , public: true },
      ]
   };
}

