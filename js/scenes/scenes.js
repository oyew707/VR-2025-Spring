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

            { name: "hud"            , path: "./hud.js"           , public: false },
            { name: "g2Example1"     , path: "./g2Example1.js"    , public: false },
            { name: "intersect2"     , path: "./intersect2.js"    , public: false },
            { name: "large_texture"  , path: "./large_texture.js" , public: false },
            { name: "combineMeshes"  , path: "./combineMeshes.js" , public: false },
            { name: "widgets"        , path: "./widgets.js"       , public: false },
            { name: "statue"         , path: "./statue.js"        , public: false },
            { name: "severalGLTF"    , path: "./severalGLTF.js"   , public: false },

            { name: "wordcloud7"     , path: "./wordcloud7.js"    , public: true  },
            { name: "stock"          , path: "./stock.js"         , public: true  },
            { name: "aiQuery-console", path: "./aiQueryConsole.js", public: true  },
            { name: "aiQuery"        , path: "./aiQuery.js"       , public: true  },
            { name: "cities"         , path: "./cities.js"        , public: true  },
            { name: "tale"           , path: "./tale.js"          , public: true  },
            { name: "art"            , path: "./art.js"           , public: true  },

            { name: "pinch"          , path: "./pinch.js"         , public: true  },
            { name: "pinch2"         , path: "./pinch2.js"        , public: true  },


      ]
   };
}

