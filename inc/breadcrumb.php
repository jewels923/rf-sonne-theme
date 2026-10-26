<?php
/**
 * 面包屑短代码
 * 用法: [breadcrumb] 或 [breadcrumb separator=">"] 或 [breadcrumb class="dark"] 或 [breadcrumb container_class="container"] 或 [breadcrumb class="float"]
 */
function breadcrumb_shortcode( $atts = array() ) {
    // 只在非首页显示
    if ( is_front_page() ) {
        return '';
    }

    static $breadcrumb_css_printed = false;

    // 解析参数
    $atts = shortcode_atts( array(
        'separator'       => '/',
        'class'           => '', // 可选: 'dark', 'compact', 'float'
        'container_class' => '',
    ), $atts );

    $separator = '<span class="wxkn-breadcrumb-separator">' . esc_html( $atts['separator'] ) . '</span>';

    // 构建包装类名
    $wrapper_class = 'wxkn-breadcrumb-wrapper';
    if ( $atts['class'] ) {
        $wrapper_class .= ' wxkn-breadcrumb--' . esc_attr( $atts['class'] );
    }
    $container_class = trim( $atts['container_class'] );
    if ( $container_class ) {
        $wrapper_class .= ' wxkn-breadcrumb-wrapper--has-container';
    }

    $breadcrumb = '';
    if ( ! $breadcrumb_css_printed ) {
        $breadcrumb .= '<style id="breadcrumb-shortcode-css">';
        $breadcrumb .= '.wxkn-breadcrumb-wrapper{padding:0.75rem 0;background-color:transparent;border-bottom:1px solid rgba(255,255,255,0.05)}';
        $breadcrumb .= '.wxkn-breadcrumb-wrapper--has-container{padding:0.75rem 0}';
        $breadcrumb .= '.wxkn-breadcrumb{display:flex;flex-wrap:wrap;align-items:center;gap:0;font-family:Rajdhani,sans-serif;font-size:14px;font-weight:500;line-height:1.5;margin-left:1rem}';
        $breadcrumb .= '.wxkn-breadcrumb-wrapper--has-container .wxkn-breadcrumb{margin-left:0}';
        $breadcrumb .= '.wxkn-breadcrumb a{color:#A1A1AA;text-decoration:none;transition:color 0.3s ease;display:inline-flex;align-items:center}';
        $breadcrumb .= '.wxkn-breadcrumb a:hover{color:#1E50FF}';
        $breadcrumb .= '.wxkn-breadcrumb a:focus-visible{outline:2px solid #1E50FF;outline-offset:2px}';
        $breadcrumb .= '.wxkn-breadcrumb-separator{color:rgba(255,255,255,0.2);margin:0 0.75rem;user-select:none}';
        $breadcrumb .= '.wxkn-breadcrumb-current{color:#F5F5F7;font-weight:600}';
        $breadcrumb .= '.wxkn-breadcrumb--dark .wxkn-breadcrumb a{color:rgba(255,255,255,0.7)}';
        $breadcrumb .= '.wxkn-breadcrumb--dark .wxkn-breadcrumb a:hover{color:#1E50FF}';
        $breadcrumb .= '.wxkn-breadcrumb--dark .wxkn-breadcrumb-separator{color:rgba(255,255,255,0.3)}';
        $breadcrumb .= '.wxkn-breadcrumb--dark .wxkn-breadcrumb-current{color:#F5F5F7}';
        $breadcrumb .= '.wxkn-breadcrumb--compact{padding:0.5rem 0;margin-bottom:0.75rem;border-bottom:none}';
        $breadcrumb .= '.wxkn-breadcrumb--compact .wxkn-breadcrumb{font-size:13px}';
        $breadcrumb .= '.wxkn-breadcrumb--compact .wxkn-breadcrumb-separator{margin:0 0.5rem}';
        // Float style - 半透明白色浮动在首屏大图左下角
        $breadcrumb .= '.wxkn-breadcrumb--float{position:absolute;bottom:20px;left:0;right:0;z-index:20;padding:0;background:none;border:none}';
        $breadcrumb .= '.wxkn-breadcrumb--float .wxkn-breadcrumb{font-size:14px;letter-spacing:0.05em;margin-left:0}';
        $breadcrumb .= '.wxkn-breadcrumb--float .wxkn-breadcrumb a{color:rgba(255,255,255,0.7)}';
        $breadcrumb .= '.wxkn-breadcrumb--float .wxkn-breadcrumb a:hover{color:rgba(255,255,255,1)}';
        $breadcrumb .= '.wxkn-breadcrumb--float .wxkn-breadcrumb-separator{color:rgba(255,255,255,0.4);margin:0 8px}';
        $breadcrumb .= '.wxkn-breadcrumb--float .wxkn-breadcrumb-current{color:rgba(255,255,255,0.85)}';
        $breadcrumb .= '@media (max-width:767px){.wxkn-breadcrumb-wrapper{padding:0.5rem 0}.wxkn-breadcrumb{font-size:13px;margin-left:0}.wxkn-breadcrumb-separator{margin:0 0.5rem}.wxkn-breadcrumb--float{bottom:12px}.wxkn-breadcrumb--float .wxkn-breadcrumb{font-size:13px}.wxkn-breadcrumb--float .wxkn-breadcrumb-separator{margin:0 6px}}';
        $breadcrumb .= '</style>';
        $breadcrumb_css_printed = true;
    }

    $breadcrumb .= '<div class="' . $wrapper_class . '">';
    if ( $container_class ) {
        $breadcrumb .= '<div class="' . esc_attr( $container_class ) . '">';
    }
    $breadcrumb .= '<nav class="wxkn-breadcrumb" itemscope itemtype="https://schema.org/BreadcrumbList">';
    $breadcrumb .= '<span itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">';
    $breadcrumb .= '<a href="' . home_url() . '" itemprop="item"><span itemprop="name">Home</span></a>';
    $breadcrumb .= '<meta itemprop="position" content="1" />';
    $breadcrumb .= '</span>';
    $breadcrumb .= $separator;

    $position = 2;

    // 页面类型
    if ( is_page() ) {
        // 获取父级页面
        $parent_id = wp_get_post_parent_id( get_the_ID() );
        if ( $parent_id ) {
            $parent_title = get_the_title( $parent_id );
            $parent_url = get_permalink( $parent_id );
            $breadcrumb .= '<span itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">';
            $breadcrumb .= '<a href="' . $parent_url . '" itemprop="item"><span itemprop="name">' . $parent_title . '</span></a>';
            $breadcrumb .= '<meta itemprop="position" content="' . $position . '" />';
            $breadcrumb .= '</span>';
            $breadcrumb .= $separator;
            $position++;
        }

        // 当前页面
        $breadcrumb .= '<span itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">';
        $breadcrumb .= '<span class="wxkn-breadcrumb-current" itemprop="name">' . get_the_title() . '</span>';
        $breadcrumb .= '<meta itemprop="position" content="' . $position . '" />';
        $breadcrumb .= '</span>';
    }

    // 单个产品
    if ( is_singular( 'product' ) ) {
        // 获取产品分类
        $terms = get_the_terms( get_the_ID(), 'product-category' );
        if ( $terms && ! is_wp_error( $terms ) ) {
            // 取第一个分类
            $term = $terms[0];

            // 检查父级分类
            if ( $term->parent != 0 ) {
                $parent_term = get_term( $term->parent, 'product-category' );
                if ( $parent_term && ! is_wp_error( $parent_term ) ) {
                    $breadcrumb .= '<span itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">';
                    $breadcrumb .= '<a href="' . get_term_link( $parent_term ) . '" itemprop="item"><span itemprop="name">' . $parent_term->name . '</span></a>';
                    $breadcrumb .= '<meta itemprop="position" content="' . $position . '" />';
                    $breadcrumb .= '</span>';
                    $breadcrumb .= $separator;
                    $position++;
                }
            }

            // 当前分类
            $breadcrumb .= '<span itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">';
            $breadcrumb .= '<a href="' . get_term_link( $term ) . '" itemprop="item"><span itemprop="name">' . $term->name . '</span></a>';
            $breadcrumb .= '<meta itemprop="position" content="' . $position . '" />';
            $breadcrumb .= '</span>';
            $breadcrumb .= $separator;
            $position++;
        }

        // 当前产品
        $breadcrumb .= '<span itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">';
        $breadcrumb .= '<span class="wxkn-breadcrumb-current" itemprop="name">' . get_the_title() . '</span>';
        $breadcrumb .= '<meta itemprop="position" content="' . $position . '" />';
        $breadcrumb .= '</span>';
    }

    // 产品分类页
    if ( is_tax( 'product-category' ) ) {
        $current_term = get_queried_object();

        // 检查父级分类
        if ( $current_term->parent != 0 ) {
            $parent_term = get_term( $current_term->parent, 'product-category' );
            if ( $parent_term && ! is_wp_error( $parent_term ) ) {
                $breadcrumb .= '<span itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">';
                $breadcrumb .= '<a href="' . get_term_link( $parent_term ) . '" itemprop="item"><span itemprop="name">' . $parent_term->name . '</span></a>';
                $breadcrumb .= '<meta itemprop="position" content="' . $position . '" />';
                $breadcrumb .= '</span>';
                $breadcrumb .= $separator;
                $position++;
            }
        }

        // 当前分类
        $breadcrumb .= '<span itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">';
        $breadcrumb .= '<span class="wxkn-breadcrumb-current" itemprop="name">' . $current_term->name . '</span>';
        $breadcrumb .= '<meta itemprop="position" content="' . $position . '" />';
        $breadcrumb .= '</span>';
    }

    $breadcrumb .= '</nav>';
    if ( $container_class ) {
        $breadcrumb .= '</div>';
    }
    $breadcrumb .= '</div>';

    return $breadcrumb;
}
add_shortcode( 'breadcrumb', 'breadcrumb_shortcode' );
